# ratios_calculator.py
import pandas as pd

def calculate_ratios(df):
    df['Net Profit Margin'] = df.apply(
        lambda row: (row['NetIncome'] / row['Revenue']) if pd.notnull(row.get('NetIncome')) and pd.notnull(row.get('Revenue')) else None,
        axis=1
    )
    df['Asset Turnover'] = df.apply(
        lambda row: (row['Revenue'] / row['TotalAssets']) if pd.notnull(row.get('Revenue')) and pd.notnull(row.get('TotalAssets')) else None,
        axis=1
    )
    df['Equity Multiplier'] = df.apply(
        lambda row: (row['TotalAssets'] / row['StockholdersEquity']) if pd.notnull(row.get('TotalAssets')) and pd.notnull(row.get('StockholdersEquity')) else None,
        axis=1
    )
    df['ROE'] = df.apply(
        lambda row: (row['Net Profit Margin'] * row['Asset Turnover'] * row['Equity Multiplier'])
        if pd.notnull(row.get('Net Profit Margin')) and pd.notnull(row.get('Asset Turnover')) and pd.notnull(row.get('Equity Multiplier')) else None,
        axis=1
    )
    df['Gross Profit Margin'] = df.apply(
        lambda row: (row['GrossProfit'] / row['Revenue']) if pd.notnull(row.get('GrossProfit')) and pd.notnull(row.get('Revenue')) else None,
        axis=1
    )
    df['Current Ratio'] = df.apply(
        lambda row: (row['CurrentAssets'] / row['CurrentLiabilities']) if pd.notnull(row.get('CurrentAssets')) and pd.notnull(row.get('CurrentLiabilities')) else None,
        axis=1
    )
    return df

# Add this to calculate_ratios.py

import pandas as pd

def calculate_dcf(financial_df):
    # Extract only the necessary fields for the DCF table
    dcf_data = []

    for _, row in financial_df.iterrows():
        year = str(int(row['Year']))  # Convert year to a string without formatting
        operating_cash_flow = row.get('OperatingCashFlow', 0)
        capital_expenditures = row.get('CapitalExpenditures', 0)

        # Check for 'DepreciationAmortization' first, then fallback to 'DepreciationDepletionAndAmortization'
        depreciation_amortization = row.get('DepreciationAmortization', 0)
        if depreciation_amortization == 0:
            depreciation_amortization = row.get('DepreciationDepletionAndAmortization', 0)
        
        interest_expense = row.get('InterestExpense', 0)
        income_tax_expense = row.get('IncomeTaxExpense', 0)
        long_term_debt = row.get('LongTermDebt', 0)
        short_term_borrowings = row.get('ShortTermBorrowings', 0)
        cash_and_cash_equivalents = row.get('CashAndCashEquivalents', 0)

        # Calculate Free Cash Flow
        free_cash_flow = operating_cash_flow - capital_expenditures

        # Placeholder WACC and Terminal Growth Rate
        wacc = 0.08
        terminal_growth_rate = 0.02

        # Calculate Terminal Value (simple perpetual growth model)
        terminal_value = free_cash_flow * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)

        dcf_data.append({
            'Year': year,  # Use string for the year without decimals
            'Operating Cash Flow': operating_cash_flow / 1_000_000,
            'Capital Expenditures': capital_expenditures / 1_000_000,
            'Free Cash Flow': free_cash_flow / 1_000_000,
            'Depreciation & Amortization': depreciation_amortization / 1_000_000,
            'Interest Expense': interest_expense / 1_000_000,
            'Income Tax Expense': income_tax_expense / 1_000_000,
            'Long Term Debt': long_term_debt / 1_000_000,
            'Short Term Borrowings': short_term_borrowings / 1_000_000,
            'Cash & Cash Equivalents': cash_and_cash_equivalents / 1_000_000,
            'Terminal Value': terminal_value / 1_000_000
        })

    dcf_df = pd.DataFrame(dcf_data)

    # Format numeric columns to three decimal points
    dcf_df.update(dcf_df.select_dtypes(include=['float']).applymap(lambda x: f"{x:,.3f}"))

    return dcf_df

