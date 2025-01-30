import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

def load_and_validate_csv(uploaded_file):
    """Load and validate the CSV file"""
    try:
        df = pd.read_csv(uploaded_file, usecols=['symbol', 'date'])
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', dayfirst=True)
        return df, None
    except Exception as e:
        return None, f"Error loading CSV: {str(e)}"

def fetch_stock_data(symbols, start_dates, max_days):
    """Fetch historical data for multiple stocks in a single request"""
    start_date = min(start_dates)
    end_date = start_date + pd.Timedelta(days=max_days)
    
    tickers = [f"{sym}.NS" for sym in symbols]
    data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', progress=False)
    
    return data

def process_stock_data(df, target_return, min_days, max_days):
    """Process stock data efficiently"""
    unique_symbols = df['symbol'].unique()
    stock_data = fetch_stock_data(unique_symbols, df['date'], max_days)
    
    results = []
    for symbol, start_date in zip(df['symbol'], df['date']):
        try:
            data = stock_data[f"{symbol}.NS"]
            start_price = data.loc[start_date, 'Close']
            high_prices = data.loc[start_date:start_date + pd.Timedelta(days=max_days), 'High']
            
            # Identify the first day hitting target return
            target_price = start_price * (1 + target_return / 100)
            hit_day = (high_prices >= target_price).idxmax()
            
            if high_prices.loc[hit_day] >= target_price:
                days_taken = (hit_day - start_date).days
                return_pct = (high_prices.loc[hit_day] - start_price) / start_price * 100
            else:
                return_pct, days_taken, target_price = None, None, None

        except Exception:
            return_pct, days_taken, start_price, target_price = None, None, None, None

        results.append([return_pct, days_taken, start_price, target_price])

    df[['return_pct', 'days_taken', 'entry_price', 'target_price']] = results
    df['target_met'] = df['return_pct'].notna()

    return df

def create_return_distribution_chart(df, target_return):
    """Create a histogram of returns"""
    successful_returns = df[df['target_met']]['return_pct']
    if successful_returns.empty:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)

    fig = px.histogram(successful_returns, nbins=30, title=f'Distribution of Returns (Target {target_return}%)',
                        labels={'value': 'Return (%)'}, color_discrete_sequence=['#FF4B4B'])
    fig.add_vline(x=target_return, line_dash="dash", line_color="green", annotation_text=f"{target_return}% Target")
    return fig

def create_success_rate_chart(df, target_return):
    """Create a pie chart showing success rate"""
    success_count = df['target_met'].sum()
    total_count = df['target_met'].count()

    if total_count == 0:
        return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)

    fig = go.Figure(data=[go.Pie(labels=[f'Hit {target_return}%', f'Below {target_return}%'], 
                                  values=[success_count, total_count - success_count], hole=.3,
                                  marker_colors=['#00CC96', '#EF553B'])])
    fig.update_layout(title=f'Success Rate ({target_return}% Target)')
    return fig
