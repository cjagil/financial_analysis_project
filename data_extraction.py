import pandas as pd

# New tags for DCF analysis
tags = {
    'Revenue': ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'TotalRevenue', 'SalesRevenueGoodsNet', 'SalesRevenueServicesNet'],
    'CostOfGoodsSold': ['CostOfGoodsSold', 'CostOfRevenue', 'CostOfGoodsAndServicesSold'],
    'GrossProfit': ['GrossProfit'],
    'CurrentAssets': ['AssetsCurrent'],
    'CurrentLiabilities': ['LiabilitiesCurrent'],
    'NetIncome': ['NetIncomeLoss'],
    'TotalAssets': ['Assets'],
    'StockholdersEquity': ['StockholdersEquity', 'Equity'],
    'OperatingCashFlow': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'],
    'CapitalExpenditures': ['CapitalExpenditures', 'PaymentsToAcquirePropertyPlantAndEquipment'],
    'DepreciationAmortization': ['DepreciationAndAmortization', 'Depreciation'],
    'InterestExpense': ['InterestExpense', 'InterestAndDebtExpense'],
    'IncomeTaxExpense': ['IncomeTaxExpenseBenefit', 'IncomeTaxPaid'],
    'LongTermDebt': ['LongTermDebt', 'LongTermDebtNoncurrent', 'LongTermDebtCurrent'],  # Include backup tags
    'ShortTermBorrowings': ['ShortTermBorrowings'],
    'CashAndCashEquivalents': ['CashAndCashEquivalentsAtCarryingValue']
}

def collect_data_points(facts, namespaces, key, tag_list, data_points, num_years):
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

    # Data processing
    if data_points[key]:
        df_temp = pd.DataFrame(data_points[key])
        df_temp['end'] = pd.to_datetime(df_temp['end'])
        df_temp.sort_values(by=['Year', 'end'], ascending=[False, False], inplace=True)
        df_temp = df_temp.drop_duplicates(subset=['Year'])
        df_temp = df_temp.head(num_years)
        if key == 'Revenue':
            df_temp = df_temp.loc[df_temp.groupby('Year')['val'].idxmax()]
        data_points[key] = df_temp.to_dict('records')

        # If no long-term debt data found, attempt to sum 'LongTermDebtCurrent' and 'LongTermDebtNoncurrent'
        if key == 'LongTermDebt' and not data_points[key]:
            long_term_debt_current = ns_data.get('LongTermDebtCurrent', {}).get('units', {}).get('USD', [])
            long_term_debt_noncurrent = ns_data.get('LongTermDebtNoncurrent', {}).get('units', {}).get('USD', [])
            combined_debt = []

            for item in long_term_debt_current + long_term_debt_noncurrent:
                if item.get('form') == '10-K':
                    end_date = item.get('end')
                    fy = int(item.get('fy')) if item.get('fy') else None
                    combined_debt.append({
                        'item': key,
                        'end': end_date,
                        'val': item.get('val'),
                        'namespace': namespace,
                        'tag': 'CombinedLongTermDebt',
                        'unit': 'USD',
                        'form': item.get('form'),
                        'Year': fy
                    })

            if combined_debt:
                df_combined = pd.DataFrame(combined_debt)
                df_combined['end'] = pd.to_datetime(df_combined['end'])
                df_combined.sort_values(by=['Year', 'end'], ascending=[False, False], inplace=True)
                df_combined = df_combined.drop_duplicates(subset=['Year'])
                df_combined = df_combined.head(num_years)
                data_points[key] = df_combined.to_dict('records')

def extract_financial_data(company_facts, num_years):
    facts = company_facts.get('facts', {})
    namespaces = ['us-gaap']
    data_points = {}

    # Collect data for all tags
    for key, tag_list in tags.items():
        collect_data_points(facts, namespaces, key, tag_list, data_points, num_years)

    return data_points

def compile_financial_data(data_points, num_years):
    df_dict = {}
    for key, items in data_points.items():
        df = pd.DataFrame(items)
        if not df.empty:
            df = df.loc[df.groupby('Year')['val'].idxmax()]
            df = df[['Year', 'val']].rename(columns={'val': key})
            df_dict[key] = df

    if not df_dict:
        print("No financial data available.")
        return pd.DataFrame()

    df_list = list(df_dict.values())
    df_merged = df_list[0]
    for df in df_list[1:]:
        df_merged = pd.merge(df_merged, df, on=['Year'], how='outer', suffixes=(None, '_dup'))
    df_merged = df_merged.loc[:, ~df_merged.columns.str.endswith('_dup')]
    df_merged.sort_values('Year', ascending=False, inplace=True)
    df_merged = df_merged.head(num_years)

    return df_merged
