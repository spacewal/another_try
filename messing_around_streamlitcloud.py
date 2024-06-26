# -*- coding: utf-8 -*-
"""Messing_around_streamLitCloud.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1l1tpMpNG5ipeu9HGy1juyvzkoIWfMxRw
"""


import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit page setup
st.title('S&P 500 Stock Analysis')

# Fetch S&P 500 tickers and sectors from Wikipedia
@st.cache_data
def load_sp500_data():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp500_table = pd.read_html(url)
    sp500_df = sp500_table[0]
    sp500_df['Symbol'] = sp500_df['Symbol'].str.replace('.', '-')
    sp500_df = sp500_df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']]
    return sp500_df

sp500_df = load_sp500_data()
tickers = sp500_df['Symbol'].tolist()

# Select ticker input
# selected_ticker = st.selectbox('Select a ticker:', tickers)

sp500_df.head()

st.header('Data')

# Define the Ichimoku Cloud calculation function
def calculate_ichimoku_cloud(df):
    tenkan_period = 9
    kijun_period = 26
    senkou_span_b_period = 52

    df['conversion_line'] = (df['High'].rolling(window=tenkan_period).max() + df['Low'].rolling(window=tenkan_period).min()) / 2
    df['base_line'] = (df['High'].rolling(window=kijun_period).max() + df['Low'].rolling(window=kijun_period).min()) / 2
    df['senkou_span_a'] = ((df['conversion_line'] + df['base_line']) / 2).shift(kijun_period)
    df['senkou_span_b'] = ((df['High'].rolling(window=senkou_span_b_period).max() + df['Low'].rolling(window=senkou_span_b_period).min()) / 2).shift(kijun_period)

    # Assuming 'last_price' is the last 'Close' price from the historical data
    last_price = df['Close'].iloc[-1]
    span_a = df['senkou_span_a'].iloc[-1]
    span_b = df['senkou_span_b'].iloc[-1]

    # Check if the last price is above the Ichimoku Cloud
    cloud_status = "ABOVE CLOUD" if last_price >= span_a and last_price >= span_b else "NOT ABOVE CLOUD"
    return cloud_status

def calculate_awesome_oscillator(df, short_period=5, long_period=34):
    # Calculate the midpoint ((High + Low) / 2) of each bar
    df['Midpoint'] = (df['High'] + df['Low']) / 2

    # Calculate the short and long period simple moving averages (SMAs) of the midpoints
    df['SMA_Short'] = df['Midpoint'].rolling(window=short_period).mean()
    df['SMA_Long'] = df['Midpoint'].rolling(window=long_period).mean()

    # Calculate the Awesome Oscillator as the difference between the short and long period SMAs
    df['AO'] = df['SMA_Short'] - df['SMA_Long']

    # Return the last value of the Awesome Oscillator series
    return df['AO'].iloc[-1]

# Define the interpretation functions
def interpret_ao(ao_value):
    return "BULLISH" if ao_value >= 0 else "BEARISH"

def interpret_ao_movement(current_ao, previous_ao):
    if current_ao >= 0 and previous_ao < current_ao:
        return "BULLISH_INCREASING"
    elif current_ao >= 0 and previous_ao > current_ao:
        return "BULLISH_DECREASING"
    elif current_ao < 0 and previous_ao < current_ao:
        return "BEARISH_INCREASING"
    elif current_ao < 0 and previous_ao > current_ao:
        return "BEARISH_DECREASING"
    return "STABLE"  # If current and previous AO values are the same

# Define the VWAP calculation function
def calculate_vwap(df):
    vwap = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap.iloc[-1]  # Return only the last value

# Define the function to calculate EMA using pandas 'ewm' method
def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# Define the function to calculate smoothed RSI
def calculate_rsi(data, periods=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()

    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))

    return RSI

# Define the function to calculate traditional RSI
def calculate_rsi_trad(data, period=14):
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    average_gain = gain.rolling(window=period).mean()
    average_loss = loss.rolling(window=period).mean()

    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

# Define the cahold function
def cahold(previous_close, latest_price):
    return "BULLISH" if latest_price >= previous_close else "BEARISH"

# Define the function to calculate MACD
def calculate_macd(df, slow_period=26, fast_period=12, signal_period=9):
    # Calculate the short-term EMA (fast period)
    ema_fast = df['Close'].ewm(span=fast_period, adjust=False).mean()

    # Calculate the long-term EMA (slow period)
    ema_slow = df['Close'].ewm(span=slow_period, adjust=False).mean()

    # Calculate the MACD line
    macd_line = ema_fast - ema_slow

    # Calculate the Signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    return macd_line, signal_line

# Define the function to calculate returns
def calculate_returns(df):
    return df['Close'].pct_change().dropna()

# Initialize an empty list to store the data
data = []

# Loop through each ticker symbol
for ticker in tickers:
    # Fetch the ticker data
    stock = yf.Ticker(ticker)

    # Get the historical data for the ticker
    hist_data = stock.history(period="1y")

    # Make sure to check if you've got enough data
    if not hist_data.empty and len(hist_data) > 1:
        # Calculate returns
        hist_data['Returns'] = calculate_returns(hist_data)

    if not hist_data.empty:
        # Calculate Ichimoku Cloud status
        cloud_status = calculate_ichimoku_cloud(hist_data)

        # Calculate Awesome Oscillator value
        ao_value = calculate_awesome_oscillator(hist_data)

        # Get the last two Awesome Oscillator values for movement interpretation
        if len(hist_data['AO']) >= 2:
            current_ao = hist_data['AO'].iloc[-1]
            previous_ao = hist_data['AO'].iloc[-2]
            ao_movement = interpret_ao_movement(current_ao, previous_ao)
        else:
            ao_movement = None

        # Calculate VWAP value
        vwap_value = calculate_vwap(hist_data)

        # Calculate each EMA
        for window in [21, 36, 50, 95, 200]:
            ema_column_name = f'EMA_{window}'
            hist_data[ema_column_name] = calculate_ema(hist_data['Close'], span=window)

        # Calculate MACD and Signal line
        hist_data['MACD'], hist_data['Signal_Line'] = calculate_macd(hist_data)

        # Calculate RSIs
        rsi_smoothed = calculate_rsi(hist_data['Close'])
        rsi_trad = calculate_rsi_trad(hist_data['Close'])

        # Calculate the cahold value
        if len(hist_data) >= 2:
          cahold_value = cahold(hist_data['Close'].iloc[-2], hist_data['Close'].iloc[-1])
        else:
          cahold_value = None

        # Append a dictionary to the data list
        stock_dict ={
            'Ticker': ticker,
            'Returns': hist_data['Returns'].iloc[-1],  # Add returns here
            'Previous_Close': hist_data['Close'].iloc[-1],
            'Volume': hist_data['Volume'].iloc[-1],
            'Cloud_Status': cloud_status,
            'Awesome_Oscillator': ao_value,
            'AO_Interpretation': interpret_ao(ao_value),
            'AO_Movement': ao_movement,
            'VWAP': vwap_value,
            'RSI_Smoothed': rsi_smoothed.iloc[-1],
            'RSI_Trad': rsi_trad.iloc[-1],
            'Cahold_Status': cahold_value
        }

        # Add EMAs to the stock dictionary
        for window in [21, 36, 50, 95, 200]:
            ema_column_name = f'EMA_{window}'
            stock_dict[ema_column_name] = hist_data[ema_column_name].iloc[-1]

        # Store the last MACD and Signal line values in the stock_dict
        stock_dict['MACD'] = hist_data['MACD'].iloc[-1]
        stock_dict['Signal_Line'] = hist_data['Signal_Line'].iloc[-1]

        # Append the dictionary to the data list
        data.append(stock_dict)

# Convert the list of dictionaries into a DataFrame
df_stocks = pd.DataFrame(data)

# Filter stocks with volume greater than 1 million
df = df_stocks[df_stocks['Volume'] > 1000000]

# Merge the dataframes on 'Ticker' and 'Symbol'
merged_df = pd.merge(df, sp500_df, left_on='Ticker', right_on='Symbol', how='left')

merged_df.drop(columns=['Symbol'], inplace=True)

merged_df = merged_df.dropna()

merged_df = merged_df.rename(columns={'GICS Sector': 'Sector'})

merged_df = merged_df.rename(columns={'GICS Sub-Industry': 'Sub_Industry'})

# Strip spaces from column names
merged_df.columns = merged_df.columns.str.strip()

# Function to create a selectbox filter
def create_filter(column_name, options):
    return st.sidebar.selectbox(f'Select filter option for {column_name}:', options)

# Define filter options
filter_options = {
    'Cloud_Status': ['ABOVE CLOUD', 'NOT ABOVE CLOUD'],
    'AO_Interpretation': ['BULLISH', 'BEARISH'],
    'AO_Movement': ['BULLISH_DECREASING', 'BEARISH_INCREASING', 'BEARISH_DECREASING'],
    'Cahold_Status': ['BULLISH', 'BEARISH']
}

# Create filters using the function
selected_filters = {key: create_filter(key, value) for key, value in filter_options.items()}

# Apply all filters at once
filtered_df = merged_df[(merged_df['Cloud_Status'] == selected_filters['Cloud_Status']) &
                 (merged_df['AO_Interpretation'] == selected_filters['AO_Interpretation']) &
                 (merged_df['AO_Movement'] == selected_filters['AO_Movement']) &
                 (merged_df['Cahold_Status'] == selected_filters['Cahold_Status'])]

# Display the filtered DataFrame
st.dataframe(filtered_df)
