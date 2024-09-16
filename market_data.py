import yfinance as yf
import pandas as pd

def get_market_data(ticker, filing_dates, num_years):
    market_data = []

    # Limit the filing dates to the specified number of years
    filing_dates = filing_dates[:num_years]

    for date in filing_dates:
        try:
            stock = yf.Ticker(ticker)
            # Fetch the closest market data available before or on the filing date
            history = stock.history(start=date, end=pd.to_datetime(date) + pd.Timedelta(days=5))
            close_price = history['Close'].values[-1] if not history.empty else None  # Get the latest available price within the range
            shares_outstanding = stock.info.get('sharesOutstanding', None)
            
            if close_price and shares_outstanding:
                market_cap = close_price * shares_outstanding
                market_data.append({
                    'Year': date[:4],  # Extract the year from the filing date
                    'ClosePrice': close_price,
                    'SharesOutstanding': shares_outstanding,
                    'MarketCap': market_cap
                })
            else:
                market_data.append({
                    'Year': date[:4],
                    'ClosePrice': None,
                    'SharesOutstanding': None,
                    'MarketCap': None
                })
        except Exception as e:
            print(f"Error retrieving market data for {ticker} on {date}: {e}")
            market_data.append({
                'Year': date[:4],
                'ClosePrice': None,
                'SharesOutstanding': None,
                'MarketCap': None
            })

    # Convert to DataFrame
    market_data_df = pd.DataFrame(market_data)
    return market_data_df
