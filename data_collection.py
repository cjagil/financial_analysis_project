# data_collection.py

import requests
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
