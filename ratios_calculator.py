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
