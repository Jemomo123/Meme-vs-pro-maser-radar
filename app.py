import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import time

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="MEXC Diamond & Meme Radar", layout="wide")

# Mobile-friendly UI enhancement
st.markdown("""
    <style>
    .stDataFrame { border: 2px solid #00FF85; border-radius: 10px; }
    h1 { color: #00FF85; font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

TIMEFRAMES = ['3m', '5m', '15m', '1h', '4h']

@st.cache_resource
def init_mexc():
    return ccxt.mexc({'enableRateLimit': True})

mexc = init_mexc()

# --- 2. MEME DETECTION LIST ---
MEME_KEYWORDS = [
    'PEPE', 'DOGE', 'SHIB', 'BONK', 'WIF', 'FLOKI', 'INU', 'MEME', 
    'BULL', 'CAT', 'MOG', 'PENGU', 'GOAT', 'BABY', 'TRUMP', 'BRETT'
]

# --- 3. THE ANALYZER ---
def get_signal(symbol, tf):
    try:
        ohlcv = mexc.fetch_ohlcv(symbol, timeframe=tf, limit=210)
        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        df['sma20'] = ta.sma(df['c'], 20)
        df['sma200'] = ta.sma(df['c'], 200)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        if prev['sma20'] < prev['sma200'] and curr['sma20'] > curr['sma200']:
            return "💎 GOLD"
        if prev['sma20'] > prev['sma200'] and curr['sma20'] < prev['sma200']:
            return "🛑 DEATH"
        if abs(curr['sma20'] - curr['sma200']) / curr['sma200'] < 0.003:
            return "🌀 SQZ"
        
        return "📈 BULL" if curr['c'] > curr['sma200'] else "📉 BEAR"
    except:
        return "-"

# --- 4. MAIN UI ---
st.title("💎 Diamond Master Radar")

# THE TOGGLE SWITCH
is_meme_mode = st.toggle("🐾 Meme Only Mode", value=False)

if st.button("🔄 Start Full Market Scan"):
    # Fetch Top 150 by Volume
    tickers = mexc.fetch_tickers()
    df_t = pd.DataFrame.from_dict(tickers, orient='index')
    df_t = df_t[df_t['symbol'].str.contains('/USDT')]
    top_coins = df_t.sort_values(by='quoteVolume', ascending=False).head(150)['symbol'].tolist()
    
    results = []
    progress_bar = st.progress(0, text="Analyzing Markets...")
    
    for i, symbol in enumerate(top_coins):
        clean_name = symbol.split('/')[0]
        is_meme = any(meme in clean_name for meme in MEME_KEYWORDS)
        
        # Filtering Logic
        if is_meme_mode and not is_meme:
            continue
            
        row = {"Coin": f"🐾 {clean_name}" if is_meme else clean_name}
        for tf in TIMEFRAMES:
            row[tf] = get_signal(symbol, tf)
        
        results.append(row)
        progress_bar.progress((i + 1) / len(top_coins))
        time.sleep(0.01) # Fast scan
    
    # Display results
    if results:
        df_final = pd.DataFrame(results)
        
        def apply_colors(val):
            if val == "💎 GOLD": return 'color: #00FF85; font-weight: bold'
            if val == "🛑 DEATH": return 'color: #FF3131'
            if val == "🌀 SQZ": return 'color: #FFA500'
            if val == "📈 BULL": return 'color: #2E7D32'
            if val == "📉 BEAR": return 'color: #C62828'
            return 'color: white'

        st.dataframe(
            df_final.style.map(apply_colors, subset=TIMEFRAMES),
            height=800, 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("No coins found matching that filter.")
