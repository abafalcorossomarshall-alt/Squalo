import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import smtplib
from email.mime.text import MIMEText
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Squalo Engine 🦈", layout="wide")

try:
    MIA_EMAIL_SISTEMA = st.secrets["SYSTEM_EMAIL"]
    PASSWORD_APP = st.secrets["EMAIL_PASSWORD"]
    TD_KEY = st.secrets["TWELVE_DATA_KEY"] # API Key di Twelve Data
except KeyError:
    st.error("Configura i Secrets: SYSTEM_EMAIL, EMAIL_PASSWORD e TWELVE_DATA_KEY")
    st.stop()

WATCHLIST_CRYPTO = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
WATCHLIST_STOCKS = ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN"]

# --- MOTORE DATI ---

def get_crypto_data(symbol):
    """Dati da Binance (Stabile)"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=4h&limit=200"
    try:
        res = requests.get(url, timeout=10).json()
        df = pd.DataFrame(res, columns=['Time', 'Open', 'High', 'Low', 'Close', 'V', 'CT', 'QA', 'NT', 'TB', 'TQ', 'I'])
        df['Close'] = df['Close'].astype(float)
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        return df.set_index('Time')
    except: return pd.DataFrame()

def get_stock_data(symbol):
    """Dati da Twelve Data (Bypassa i blocchi Yahoo)"""
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=4h&apikey={TD_KEY}&outputsize=200"
    try:
        res = requests.get(url).json()
        df = pd.DataFrame(res['values'])
        df['close'] = df['close'].astype(float)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.rename(columns={'close': 'Close', 'datetime': 'Time'}).set_index('Time')
        return df.sort_index()
    except: return pd.DataFrame()

def calcola_indicatori(df):
    if df.empty: return df
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=13, adjust=False).mean()
    ma_down = down.ewm(com=13, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, 0.00001)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- INTERFACCIA ---
st.sidebar.title("🦈 Squalo Engine")
menu = st.sidebar.selectbox("Menu", ["Scanner Squalo", "Dashboard Live"])

if menu == "Scanner Squalo":
    st.header("🌊 Scanner Multi-API (Binance + TwelveData)")
    target_mail = st.text_input("Email Alert", "tua@email.com")
    
    if st.button("Avvia Scansione"):
        results = []
        # Crypto
        for t in WATCHLIST_CRYPTO:
            df = calcola_indicatori(get_crypto_data(t))
            if not df.empty:
                p, e, r = df['Close'].iloc[-1], df['EMA200'].iloc[-1], df['RSI'].iloc[-1]
                stato = "🔥 COMPRA" if (p > e and 40 <= r <= 55) else "ATTESA"
                results.append({"Ticker": t, "Prezzo": p, "RSI": round(r,2), "Stato": stato})
        
        # Stocks
        for t in WATCHLIST_STOCKS:
            df = calcola_indicatori(get_stock_data(t))
            if not df.empty:
                p, e, r = df['Close'].iloc[-1], df['EMA200'].iloc[-1], df['RSI'].iloc[-1]
                stato = "🔥 COMPRA" if (p > e and 40 <= r <= 55) else "ATTESA"
                results.append({"Ticker": t, "Prezzo": p, "RSI": round(r,2), "Stato": stato})
            time.sleep(8) # Limite Twelve Data Free (8 richieste/min)

        st.table(pd.DataFrame(results))

elif menu == "Dashboard Live":
    ticker = st.text_input("Ticker (es. AAPL o BTCUSDT)", "BTCUSDT").upper()
    df = get_crypto_data(ticker) if "USDT" in ticker else get_stock_data(ticker)
    df = calcola_indicatori(df)
    
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Prezzo"))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name="EMA200", line=dict(dash='dash')))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        # DESCRIZIONI (Richieste)
        st.subheader("🧐 Analisi Tecnica")
        c1, c2 = st.columns(2)
        p, e, r = df['Close'].iloc[-1], df['EMA200'].iloc[-1], df['RSI'].iloc[-1]
        
        with c1:
            if p > e: st.success(f"Trend Rialzista: Prezzo sopra EMA200.")
            else: st.error("Trend Ribassista: Prezzo sotto EMA200.")
        with c2:
            st.info(f"RSI a {r:.2f}: " + ("Zona Ricarica ✅" if 40<=r<=55 else "Nessun segnale."))
