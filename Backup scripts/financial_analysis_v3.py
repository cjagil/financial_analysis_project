import requests
import pandas as pd
import json
from datetime import datetime

def get_cik_from_ticker(ticker):
    url = 'https://www.sec.gov/files/company_tickers.json'
    headers = {
        'User-Agent': 'Curtis Gile (curtis.j.gile@gmail.com)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        ticker_data = response.json()
        for entry in ticker_data.values():
            if entry['ticker'].lower() == ticker.lower():
                print(f"Found CIK for ticker {ticker}: {entry['cik_str']}")
                return int(entry['cik_str'])
    print(f"Could not find CIK for ticker: {ticker}")
    return None

def get_company_facts(cik):
    url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json'
    headers = {
        'User-Agent': 'Curtis Gile (curtis.j.gile@gmail.com)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        company_facts = response.json()
        # Save the full output to a JSON file for manual inspection
        with open('sec_company_facts.json', 'w') as f:
            json.dump(company_facts, f, indent=2)
        print("The full company facts have been saved to 'sec_company_facts.json'.")
        return company_facts
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

def extract_financial_data(company_facts):
    facts = company_facts.get('facts', {})
    data_points = {}

    # List of potential revenue tags
    revenue_tags = [
        'Revenues',
        'SalesRevenueNet',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'TotalRevenue',
        'SalesRevenueGoodsNet',
        'SalesRevenueServicesNet'
    ]
    namespaces = ['us-gaap']

    # Other financial items and their tags
    tags = {
        'Revenue': revenue_tags,
        'CostOfGoodsSold': ['CostOfGoodsSold', 'CostOfRevenue', 'CostOfGoodsAndServicesSold'],
        'GrossProfit': ['GrossProfit'],
        'CurrentAssets': ['AssetsCurrent'],
        'CurrentLiabilities': ['LiabilitiesCurrent'],
        'NetIncome': ['NetIncomeLoss'],
        'TotalAssets': ['Assets'],
        'StockholdersEquity': ['StockholdersEquity', 'Equity']
    }

    # Helper function to collect data points for a given key
    def collect_data_points(key, tag_list, data_points):
        data_points[key] = []
        for namespace in namespaces:
            ns_data = facts.get(namespace, {})
            for tag_name in tag_list:
                tag_data = ns_data.get(tag_name)
                if tag_data and 'units' in tag_data:
                    for unit, values in tag_data['units'].items():
                        for item in values:
                            if item.get('form') == '10-K':  # Filter to 10-K forms
                                end_date = item.get('end')
                                fy = int(item.get('fy')) if item.get('fy') else None

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

        # Convert to DataFrame and sort by 'end' to get the latest entries
        if data_points[key]:
            df_temp = pd.DataFrame(data_points[key])
            # Sort by 'end' date descending
            df_temp['end'] = pd.to_datetime(df_temp['end'])
            df_temp.sort_values(by='end', ascending=False, inplace=True)
            # Filter to only the last three years
            df_temp = df_temp.drop_duplicates(subset=['Year']).head(3)
            # For revenue, pick the maximum value for the year of the 10-K statement
            if key == 'Revenue':
                df_temp = df_temp.loc[df_temp.groupby('Year')['val'].idxmax()]
            data_points[key] = df_temp.to_dict('records')
        print(f"Collected {len(data_points[key])} data points for {key}.")

    # Collect revenue data points using the updated tags
    collect_data_points('Revenue', revenue_tags, data_points)

    # Collect other financial data points
    for key, tag_list in tags.items():
        if key != 'Revenue':  # We've already handled revenue separately
            collect_data_points(key, tag_list, data_points)

    return data_points

def compile_financial_data(data_points):
    # Create DataFrames for each item
    df_dict = {}
    for key, items in data_points.items():
        df = pd.DataFrame(items)
        if not df.empty:
            # Ensure one value per 'Year' by keeping the maximum
            df = df.loc[df.groupby('Year')['val'].idxmax()]
            # Select only necessary columns for merging
            df = df[['Year', 'val']].rename(columns={'val': key})
            df_dict[key] = df
            print(f"Data points for {key}:")
            print(df)

    if not df_dict:
        print("No financial data available.")
        return pd.DataFrame()

    # Merge DataFrames on 'Year' using outer join
    df_list = list(df_dict.values())
    df_merged = df_list[0]
    for df in df_list[1:]:
        df_merged = pd.merge(df_merged, df, on=['Year'], how='outer', suffixes=(None, '_dup'))
    
    # Remove duplicate columns caused by the merge
    df_merged = df_merged.loc[:, ~df_merged.columns.str.endswith('_dup')]

    # Sort by 'Year' descending and limit to the three most recent years
    df_merged.sort_values('Year', ascending=False, inplace=True)
    df_merged = df_merged.head(3)

    return df_merged

def calculate_ratios(df):
    # Calculate Net Profit Margin
    df['Net Profit Margin'] = df.apply(
        lambda row: (row['NetIncome'] / row['Revenue']) if pd.notnull(row.get('NetIncome')) and pd.notnull(row.get('Revenue')) else None,
        axis=1
    )
    
    # Calculate Asset Turnover
    df['Asset Turnover'] = df.apply(
        lambda row: (row['Revenue'] / row['TotalAssets']) if pd.notnull(row.get('Revenue')) and pd.notnull(row.get('TotalAssets')) else None,
        axis=1
    )
    
    # Calculate Equity Multiplier
    df['Equity Multiplier'] = df.apply(
        lambda row: (row['TotalAssets'] / row['StockholdersEquity']) if pd.notnull(row.get('TotalAssets')) and pd.notnull(row.get('StockholdersEquity')) else None,
        axis=1
    )
    
    # Calculate ROE using the DuPont formula
    df['ROE'] = df.apply(
        lambda row: (row['Net Profit Margin'] * row['Asset Turnover'] * row['Equity Multiplier'])
        if pd.notnull(row.get('Net Profit Margin')) and pd.notnull(row.get('Asset Turnover')) and pd.notnull(row.get('Equity Multiplier')) else None,
        axis=1
    )

    # Calculate Gross Profit Margin and Current Ratio (existing calculations)
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
    # Prompt the user for a ticker symbol or CIK number
    user_input = input("Enter a ticker symbol or CIK number: ").strip()
    
    # Determine if the input is a ticker or CIK
    ticker = None
    if user_input.isdigit():
        cik = int(user_input)
    else:
        ticker = user_input
        cik = get_cik_from_ticker(user_input)
        if cik is None:
            return

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

    # Calculate ratios including ROE and DuPont components
    df = calculate_ratios(df)

    # Select and rename columns for display
    df_display = df[['Year', 'Revenue', 'NetIncome', 'TotalAssets', 'StockholdersEquity',
                     'Net Profit Margin', 'Asset Turnover', 'Equity Multiplier', 'ROE',
                     'Gross Profit Margin', 'CurrentAssets', 'CurrentLiabilities', 'Current Ratio']].copy()

    df_display = df_display.rename(columns={
        'NetIncome': 'Net Income',
        'TotalAssets': 'Total Assets',
        'StockholdersEquity': 'Shareholders\' Equity',
        'CostOfGoodsSold': 'Cost of Goods Sold',
        'GrossProfit': 'Gross Profit',
        'CurrentAssets': 'Current Assets',
        'CurrentLiabilities': 'Current Liabilities',
        'Year': 'Reporting Year'
    })

    # Print the final DataFrame
    pd.options.display.float_format = '{:,.2f}'.format
    print(df_display)

if __name__ == '__main__':
    main()
