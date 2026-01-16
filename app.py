import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh

# --- MOBILE CONFIG & AUTO-REFRESH ---
st.set_page_config(page_title="MEXC 1m Radar", layout="wide")
count = st_autorefresh(interval=60000, key="mexc_heartbeat")

@st.cache_resource
def init_mexc():
    return ccxt.mexc({'enableRateLimit': True})

mexc = init_mexc()

def get_mexc_link(symbol):
    pair = symbol.replace("/", "_")
    url = f"https://www.mexc.com/exchange/{pair}"
    return f'<a href="{url}" target="_blank" style="text-decoration: none; background-color: #00FF85; color: black; padding: 5px 10px; border-radius: 8px; font-weight: bold;">⚡ TRADE</a>'

def analyze_market(symbol, tf):
    try:
        ohlcv = mexc.fetch_ohlcv(symbol, timeframe=tf, limit=210)
        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        sma20, sma200 = ta.sma(df['c'], 20), ta.sma(df['c'], 200)
        vwap = ta.vwap(df['h'], df['l'], df['c'], df['v']).iloc[-1]
        curr_p = df['c'].iloc[-1]
        
        ob = mexc.fetch_order_book(symbol, limit=20)
        bids, asks = sum([b[1] for b in ob['bids']]), sum([a[1] for a in ob['asks']])
        opp_ratio = bids / asks if asks > 0 else 10
        
        gap = ((curr_p - vwap) / vwap) * 100
        sig = "·"
        if sma20.iloc[-2] < sma200.iloc[-2] and sma20.iloc[-1] > sma200.iloc[-1]: sig = "💎 GOLD"
        elif sma20.iloc[-2] > sma200.iloc[-2] and sma20.iloc[-1] < sma200.iloc[-1]: sig = "💀 DEATH"
        elif abs(sma20.iloc[-1] - sma200.iloc[-1]) / sma200.iloc[-1] < 0.003: sig = "🌀 SQZ"

        return sig, round(gap, 2), round(opp_ratio, 1)
    except: return "err", 0, 1

# --- UI DISPLAY ---
btc = mexc.fetch_ticker('BTC/USDT')
st.subheader(f"Market Bias: {'🔥 BULL' if btc['last'] > 95000 else '⚠️ CAUTION'} | BTC: ${btc['last']:,.0f}")

tickers = mexc.fetch_tickers()
top_symbols = sorted([s for s in tickers.keys() if '/USDT' in s], key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:30]

data = []
for s in top_symbols:
    sig, gap, opp = analyze_market(s, '15m')
    data.append({"Coin": s.replace('/USDT', ''), "Signal": sig, "VWAP Gap%": gap, "Opp. Ratio": opp, "Action": get_mexc_link(s)})

st.write(pd.DataFrame(data).to_html(escape=False, index=False), unsafe_allow_html=True)
