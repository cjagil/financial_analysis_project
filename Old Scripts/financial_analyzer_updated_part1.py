
import requests
import pandas as pd
import json
import yfinance as yf
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
        'SharesOutstanding': ['CommonStockSharesOutstanding']
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

    # Format numerical values
    pd.options.display.float_format = '{:,.2f}'.format
    
    # Display market cap information if available
    if market_cap:
        print(f"Market Capitalization: {market_cap:,.2f} USD")

    # Rename columns for display
    df_display = df_display.rename(columns={
        'CostOfGoodsSold': 'Cost of Goods Sold',
        'GrossProfit': 'Gross Profit',
        'CurrentAssets': 'Current Assets',
        'CurrentLiabilities': 'Current Liabilities',
        'Year': 'Reporting Year'
    })

    # Print the final DataFrame
    print(df_display)

if __name__ == '__main__':
    main()

