# data_extraction.py
import requests
import pandas as pd
import json

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

    revenue_tags = [
        'Revenues',
        'SalesRevenueNet',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'TotalRevenue',
        'SalesRevenueGoodsNet',
        'SalesRevenueServicesNet'
    ]
    namespaces = ['us-gaap']

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

    def collect_data_points(key, tag_list, data_points):
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
            df_temp = pd.DataFrame(data_points[key])
            df_temp['end'] = pd.to_datetime(df_temp['end'])
            df_temp.sort_values(by='end', ascending=False, inplace=True)
            df_temp = df_temp.drop_duplicates(subset=['Year']).head(3)
            if key == 'Revenue':
                df_temp = df_temp.loc[df_temp.groupby('Year')['val'].idxmax()]
            data_points[key] = df_temp.to_dict('records')
        print(f"Collected {len(data_points[key])} data points for {key}.")

    collect_data_points('Revenue', revenue_tags, data_points)
    for key, tag_list in tags.items():
        if key != 'Revenue':
            collect_data_points(key, tag_list, data_points)

    return data_points

def compile_financial_data(data_points):
    df_dict = {}
    for key, items in data_points.items():
        df = pd.DataFrame(items)
        if not df.empty:
            df = df.loc[df.groupby('Year')['val'].idxmax()]
            df = df[['Year', 'val']].rename(columns={'val': key})
            df_dict[key] = df
            print(f"Data points for {key}:")
            print(df)

    if not df_dict:
        print("No financial data available.")
        return pd.DataFrame()

    df_list = list(df_dict.values())
    df_merged = df_list[0]
    for df in df_list[1:]:
        df_merged = pd.merge(df_merged, df, on=['Year'], how='outer', suffixes=(None, '_dup'))
    df_merged = df_merged.loc[:, ~df_merged.columns.str.endswith('_dup')]
    df_merged.sort_values('Year', ascending=False, inplace=True)
    df_merged = df_merged.head(3)
    return df_merged
