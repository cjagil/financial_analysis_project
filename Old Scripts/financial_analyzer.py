import requests
import pandas as pd
import json
import re
from datetime import datetime
from functools import reduce

def get_company_facts(cik):
    url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json'
    headers = {
        'User-Agent': 'Curtis Gile (curtis.j.gile@gmail.com)',  # Updated User-Agent
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        company_facts = response.json()
        return company_facts
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

def extract_financial_data(company_facts):
    facts = company_facts.get('facts', {})
    # Initialize data storage
    data_points = {}
    current_year = datetime.now().year

    # Dynamically find all tags that contain 'revenue' in their name
    revenue_tags = []
    namespaces = ['us-gaap', 'aapl']  # You can include other namespaces if necessary
    for namespace in namespaces:
        ns_data = facts.get(namespace, {})
        for tag_name in ns_data.keys():
            if 'revenue' in tag_name.lower():
                revenue_tags.append((namespace, tag_name))
    revenue_tags = list(set(revenue_tags))  # Remove duplicates

    # Other financial items and their tags
    tags = {
        'CostOfGoodsSold': [
            'CostOfGoodsSold',
            'CostOfRevenue',
            'CostOfGoodsAndServicesSold'
        ],
        'GrossProfit': [
            'GrossProfit'
        ],
        'CurrentAssets': ['AssetsCurrent'],
        'CurrentLiabilities': ['LiabilitiesCurrent']
    }

    # Collect revenue data
    data_points['Revenue'] = []
    for namespace, tag_name in revenue_tags:
        ns_data = facts.get(namespace, {})
        tag_data = ns_data.get(tag_name)
        if tag_data and 'units' in tag_data:
            for unit, values in tag_data['units'].items():
                for item in values:
                    if item.get('form') == '10-K':
                        end_date = item.get('end')
                        fy = int(item.get('fy')) if item.get('fy') else None
                        if fy and fy <= current_year:
                            data_point = {
                                'item': 'Revenue',
                                'end': end_date,
                                'val': item.get('val'),
                                'namespace': namespace,
                                'tag': tag_name,
                                'unit': unit,
                                'form': item.get('form'),
                                'Year': fy
                            }
                            data_points['Revenue'].append(data_point)
    if data_points['Revenue']:
        print(f"Collected {len(data_points['Revenue'])} data points for Revenue from tags containing 'revenue'.")

    # Collect data for other financial items
    for key, tag_list in tags.items():
        data_points[key] = []
        for namespace in namespaces:
            ns_data = facts.get(namespace, {})
            for tag_name in tag_list:
                tag_data = ns_data.get(tag_name)
                if tag_data and 'units' in tag_data:
                    for unit, values in tag_data['units'].items():
                        for item in values:
                            if item.get('form') == '10-K':
                                end_date = item.get('end')
                                fy = int(item.get('fy')) if item.get('fy') else None
                                if fy and fy <= current_year:
                                    data_point = {
                                        'item': key,
                                        'end': end_date,
                                        'val': item.get('val'),
                                        'namespace': namespace,
                                        'tag': tag_name,
                                        'unit': unit,
                                        'form': item.get('form'),
                                        'Year': fy
                                    }
                                    data_points[key].append(data_point)
                    if data_points[key]:
                        print(f"Collected {len(data_points[key])} data points for {key} with tag '{tag_name}' in namespace '{namespace}'.")
                        break  # Break after processing the first available unit
            if data_points[key]:
                break  # Break if data found for this key
        if not data_points[key]:
            print(f"No data found for {key}")
    return data_points

def compile_financial_data(data_points):
    # Create DataFrames for each item
    df_dict = {}
    for key, items in data_points.items():
        df = pd.DataFrame(items)
        if not df.empty:
            # Convert 'end' to datetime
            df['end'] = pd.to_datetime(df['end'])
            # Keep only 10-K filings
            df = df[df['form'] == '10-K']
            # Keep only necessary columns
            df = df[['Year', 'val']]
            df = df.rename(columns={'val': key})
            df_dict[key] = df
    if not df_dict:
        print("No financial data available.")
        return pd.DataFrame()

    # Special handling for Revenue: group by 'Year' and take the maximum value
    if 'Revenue' in df_dict:
        df_revenue = df_dict['Revenue']
        df_revenue = df_revenue.groupby(['Year'], as_index=False)['Revenue'].max()
        df_dict['Revenue'] = df_revenue

    # Merge DataFrames on 'Year' using outer join
    df_list = list(df_dict.values())
    df_merged = df_list[0]
    for df in df_list[1:]:
        df_merged = pd.merge(df_merged, df, on=['Year'], how='outer')
    if df_merged.empty:
        print("No matching financial data across items.")
        return pd.DataFrame()

    # Sort by 'Year' descending
    df_merged.sort_values('Year', ascending=False, inplace=True)
    # Get last three periods
    df_merged = df_merged.drop_duplicates(subset=['Year']).head(3)

    return df_merged

def calculate_ratios(df):
    # Handle missing values by filling with NaN
    df['Gross Profit Margin'] = df.apply(
        lambda row: (row['GrossProfit'] / row['Revenue']) if pd.notnull(row.get('GrossProfit')) and pd.notnull(row.get('Revenue')) else None,
        axis=1
    )
    df['Current Ratio'] = df.apply(
        lambda row: (row['CurrentAssets'] / row['CurrentLiabilities']) if pd.notnull(row.get('CurrentAssets')) and pd.notnull(row.get('CurrentLiabilities')) else None,
        axis=1
    )
    return df

def main():
    # Apple's CIK is 0000320193
    cik = 320193
    company_facts = get_company_facts(cik)
    if not company_facts:
        return

    # Extract financial data
    data_points = extract_financial_data(company_facts)
    if not data_points:
        print("No financial data extracted.")
        return

    # Compile financial data into a DataFrame
    df = compile_financial_data(data_points)
    if df.empty:
        print("No financial data to display.")
        return

    # Calculate ratios
    df = calculate_ratios(df)
    # Select and rename columns for display
    df_display = df[['Year', 'Revenue', 'CostOfGoodsSold', 'GrossProfit',
                     'Gross Profit Margin', 'CurrentAssets', 'CurrentLiabilities',
                     'Current Ratio']].copy()
    df_display = df_display.rename(columns={
        'CostOfGoodsSold': 'Cost of Goods Sold',
        'GrossProfit': 'Gross Profit',
        'CurrentAssets': 'Current Assets',
        'CurrentLiabilities': 'Current Liabilities',
        'Year': 'Reporting Year'
    })
    # Format numerical values
    pd.options.display.float_format = '{:,.2f}'.format
    print(df_display)

if __name__ == '__main__':
    main()
