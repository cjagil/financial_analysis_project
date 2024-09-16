# Fin_ratios_main.py
import pandas as pd
from data_extraction import get_cik_from_ticker, get_company_facts, extract_financial_data, compile_financial_data
from ratios_calculator import calculate_ratios
from market_data import get_market_data


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

    # Retrieve company facts
    company_facts = get_company_facts(cik)
    if not company_facts:
        return

    # Extract financial data
    data_points = extract_financial_data(company_facts)
    if not data_points:
        print("No financial data extracted.")
        return

    # Compile financial data into a DataFrame
    financial_df = compile_financial_data(data_points)
    if financial_df.empty:
        print("No financial data to display.")
        return

# Extract filing dates for market data retrieval
    filing_dates = financial_df['Year'].apply(lambda x: f"{x}-12-31").tolist()

    # Get market data
    market_df = get_market_data(ticker, filing_dates)

    # Ensure 'Year' column is of the same type in both DataFrames
    financial_df['Year'] = financial_df['Year'].astype(int)
    market_df['Year'] = market_df['Year'].astype(int)

    # Merge financial data with market data based on the 'Year' column
    final_df = pd.merge(financial_df, market_df, on='Year', how='left', suffixes=('_financial', '_market'))

    # Calculate ratios using the merged data
    df = calculate_ratios(final_df)

    # Select and rename columns for display, including MarketCap
    df_display = df[['Year', 'Revenue', 'NetIncome', 'TotalAssets', 'StockholdersEquity',
                     'Net Profit Margin', 'Asset Turnover', 'Equity Multiplier', 'ROE',
                     'Gross Profit Margin', 'CurrentAssets', 'CurrentLiabilities', 'Current Ratio', 'MarketCap']].copy()

    df_display = df_display.rename(columns={
        'NetIncome': 'Net Income',
        'TotalAssets': 'Total Assets',
        'StockholdersEquity': 'Shareholders\' Equity',
        'CurrentAssets': 'Current Assets',
        'CurrentLiabilities': 'Current Liabilities',
        'MarketCap': 'Market Cap',
        'Year': 'Reporting Year'
    })

    # Print the final DataFrame
    pd.options.display.float_format = '{:,.2f}'.format
    print(df_display)

if __name__ == '__main__':
    main()

