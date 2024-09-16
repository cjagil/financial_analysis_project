# Fin_ratios_main.py
import pandas as pd
from data_extraction import get_cik_from_ticker, get_company_facts, extract_financial_data, compile_financial_data
from ratios_calculator import calculate_ratios
from market_data import get_market_data

import tkinter as tk
from tkinter import ttk
from tabulate import tabulate

def display_in_gui(df):
    # Create the main window
    root = tk.Tk()
    root.title("Financial Ratios Output")

    # Create a frame for the Treeview
    frame = ttk.Frame(root)
    frame.pack(padx=10, pady=10, fill='both', expand=True)

    # Create the Treeview widget with horizontal scrollbar support
    tree = ttk.Treeview(frame, columns=list(df.columns), show='headings')

    # Add a vertical scrollbar to the Treeview
    vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    vsb.pack(side='right', fill='y')
    tree.configure(yscroll=vsb.set)

    # Add a horizontal scrollbar to the Treeview
    hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
    hsb.pack(side='bottom', fill='x')
    tree.configure(xscroll=hsb.set)

    # Pack the Treeview
    tree.pack(side='left', fill='both', expand=True)

    # Define the columns
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center', width=120)

    # Insert data into the Treeview
    for index, row in df.iterrows():
        tree.insert('', 'end', values=list(row))

    # Run the application
    root.mainloop()

def main():
    # Prompt the user for a ticker symbol or CIK number
    user_input = input("Enter a ticker symbol or CIK number: ").strip()

    # Prompt the user for the number of years to extract data for
    try:
        num_years = int(input("Enter the number of years to extract data for: "))
        if num_years <= 0:
            raise ValueError("Number of years must be positive.")
    except ValueError as e:
        print(f"Invalid input: {e}")
        return

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

    # Extract financial data with num_years
    data_points = extract_financial_data(company_facts, num_years)
    if not data_points:
        print("No financial data extracted.")
        return

    # Compile financial data into a DataFrame
    financial_df = compile_financial_data(data_points, num_years)  # Pass num_years to compile_financial_data
    if financial_df.empty:
        print("No financial data to display.")
        return

    # Extract filing dates for market data retrieval
    filing_dates = financial_df['Year'].apply(lambda x: f"{x}-12-31").tolist()

    # Get market data
    market_df = get_market_data(ticker, filing_dates, num_years)

    # Ensure 'Year' column is of the same type in both DataFrames
    financial_df['Year'] = financial_df['Year'].astype(int)
    market_df['Year'] = market_df['Year'].astype(int)

    # Merge financial data with market data based on the 'Year' column
    final_df = pd.merge(financial_df, market_df, on='Year', how='left', suffixes=('_financial', '_market'))

    # Calculate ratios using the merged data
    df = calculate_ratios(final_df)

    # Convert specific columns to millions of dollars
    columns_to_convert = ['Revenue', 'NetIncome', 'TotalAssets', 'StockholdersEquity', 'CurrentAssets', 'CurrentLiabilities', 'MarketCap']
    for col in columns_to_convert:
        df[col] = df[col] / 1_000_000

    # Select and rename columns for display, including MarketCap
    df_display = df[['Year', 'Revenue', 'NetIncome', 'TotalAssets', 'StockholdersEquity',
                     'Net Profit Margin', 'Asset Turnover', 'Equity Multiplier', 'ROE',
                     'Gross Profit Margin', 'CurrentAssets', 'CurrentLiabilities', 'Current Ratio', 'MarketCap']].copy()

    df_display = df_display.rename(columns={
        'NetIncome': 'Net Income (Millions)',
        'TotalAssets': 'Total Assets (Millions)',
        'StockholdersEquity': 'Shareholders\' Equity (Millions)',
        'CurrentAssets': 'Current Assets (Millions)',
        'CurrentLiabilities': 'Current Liabilities (Millions)',
        'Year': 'Reporting Year',
        'Revenue': 'Revenue (Millions)',
        'MarketCap': 'Market Cap (Millions)'
    })

    # Convert 'Year' column to string to avoid formatting it with decimals
    df_display['Reporting Year'] = df_display['Reporting Year'].astype(str)

    # Format all numeric columns to three decimal points
    df_display = df_display.applymap(lambda x: f"{x:,.3f}" if isinstance(x, (int, float)) else x)

    # Display the final DataFrame in the GUI
    display_in_gui(df_display)

if __name__ == '__main__':
    main()
