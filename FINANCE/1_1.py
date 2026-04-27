import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import smtplib
from email.mime.text import MIMEText
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Squalo Dashboard 🦈", layout="wide")

# --- RECUPERO SICURO CREDENZIALI ---
try:
    MIA_EMAIL_SISTEMA = st.secrets["SYSTEM_EMAIL"]
    PASSWORD_APP = st.secrets["EMAIL_PASSWORD"]
except KeyError:
    st.error("Configura 'SYSTEM_EMAIL' e 'EMAIL_PASSWORD' nei Secrets di Streamlit!")
    st.stop()

# Watchlist separate per stabilità
CRYPTO_LIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
STOCKS_LIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "JPM", "GS", "V", "WMT", "KO", "DIS", "XOM", "LLY"]

# --- FUNZIONI TECNICHE ---

def get_binance_data(symbol, interval='4h', limit=300):
    """Recupera dati da Binance (Stabile su Cloud)"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        df = pd.DataFrame(data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVolume', 'NumberTrades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
        df['Close'] = df['Close'].astype(float)
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        df.set_index('Time', inplace=True)
        return df
    except:
        return pd.DataFrame()

def calcola_rsi(data, window=14):
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=window - 1, adjust=False).mean()
    ma_down = down.ewm(com=window - 1, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, 0.00001)
    return 100 - (100 / (1 + rs))

def invia_email_alert(destinatario, ticker, prezzo, rsi):
    oggetto = f"🦈 SQUALO ALERT: {ticker} a {prezzo:.2f}"
    corpo = f"Segnale rilevato per {ticker}!\nPrezzo: {prezzo:.2f}\nRSI: {rsi:.2f}\nLogica: Trend Rialzista e RSI in zona ricarica."
    msg = MIMEText(corpo)
    msg['Subject'] = oggetto
    msg['From'] = MIA_EMAIL_SISTEMA
    msg['To'] = destinatario
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MIA_EMAIL_SISTEMA, PASSWORD_APP)
            server.send_message(msg)
        return True
    except:
        return False

# --- SIDEBAR ---
st.sidebar.title("🦈 Squalo Engine")
st.sidebar.info("Modalità Ibrida Cloud Attiva")
menu = st.sidebar.selectbox("Menu Principale", 
    ["Dashboard Live", "Scanner Automatico", "Backtest Strategia", "Calcolatore TP/SL"])

# --- 1. DASHBOARD LIVE ---
if menu == "Dashboard Live":
    st.header("📈 Analisi Grafica Interattiva")
    ticker_input = st.text_input("Inserisci Ticker (es. NVDA o BTCUSDT)", "NVDA").upper()
    
    if "USDT" in ticker_input:
        data = get_binance_data(ticker_input)
    else:
        data = yf.download(ticker_input, period="1y", interval="1h", progress=False)
        if not data.empty and isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

    if data is None or data.empty:
        st.error(f"⚠️ Impossibile recuperare dati. Yahoo potrebbe aver bloccato la richiesta.")
    else:
        data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()
        data['RSI'] = calcola_rsi(data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Prezzo", line=dict(color='#4466FF')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name="EMA 200", line=dict(dash='dash', color='orange')))
        fig.update_layout(height=500, template="plotly_dark", title=f"Analisi {ticker_input}")
        st.plotly_chart(fig, use_container_width=True)
        
        p_att = float(data['Close'].iloc[-1])
        r_att = float(data['RSI'].iloc[-1])
        e_att = float(data['EMA200'].iloc[-1])

        c1, c2, c3 = st.columns(3)
        c1.metric("Prezzo", f"${p_att:,.2f}")
        c2.metric("RSI", f"{r_att:.2f}")
        is_bullish = p_att > e_att
        c3.metric("Trend", "BULLISH ✅" if is_bullish else "BEARISH ⚠️")

# --- 2. SCANNER AUTOMATICO ---
elif menu == "Scanner Automatico":
    st.header("🌊 Scanner Squalo Ibrido")
    dest_mail = st.text_input("Mail per Alert", "tua@email.com")
    
    if st.button("Avvia Scansione Ora"): 
        ris = []
        bar = st.progress(0)
        totale = len(CRYPTO_LIST) + len(STOCKS_LIST)
        
        # Scansione Crypto (Velocissima e sicura)
        for i, t in enumerate(CRYPTO_LIST):
            bar.progress((i + 1) / totale)
            d = get_binance_data(t)
            if not d.empty:
                d['EMA200'] = d['Close'].ewm(span=200, adjust=False).mean()
                d['RSI'] = calcola_rsi(d)
                p, e, r = d['Close'].iloc[-1], d['EMA200'].iloc[-1], d['RSI'].iloc[-1]
                stato = "🔥 COMPRA" if (p > e and 40 <= r <= 55) else "ATTESA"
                if stato == "🔥 COMPRA": invia_email_alert(dest_mail, t, p, r)
                ris.append({"Ticker": t, "Prezzo": round(p, 2), "RSI": round(r, 2), "Stato": stato})

        # Scansione Stock (Con delay per evitare ban)
        for i, t in enumerate(STOCKS_LIST):
            bar.progress((len(CRYPTO_LIST) + i + 1) / totale)
            try:
                d = yf.download(t, period="60d", interval="1h", progress=False)
                if not d.empty:
                    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
                    d_4h = d.resample('4H').last().dropna()
                    if len(d_4h) > 50:
                        d_4h['EMA200'] = d_4h['Close'].ewm(span=200, adjust=False).mean()
                        d_4h['RSI'] = calcola_rsi(d_4h)
                        p, e, r = d_4h['Close'].iloc[-1], d_4h['EMA200'].iloc[-1], d_4h['RSI'].iloc[-1]
                        stato = "🔥 COMPRA" if (p > e and 40 <= r <= 55) else "ATTESA"
                        if stato == "🔥 COMPRA": invia_email_alert(dest_mail, t, p, r)
                        ris.append({"Ticker": t, "Prezzo": round(p, 2), "RSI": round(r, 2), "Stato": stato})
                time.sleep(2.5) # Ritardo fondamentale su Cloud
            except: continue
        
        if ris: st.table(pd.DataFrame(ris))
        else: st.error("Errore critico: Yahoo Finance ha bloccato tutte le richieste azioni.")

# --- 3. BACKTEST E 4. CALCOLATORE (Invariati) ---
elif menu == "Backtest Strategia":
    st.header("🧪 Backtest")
    tk = st.text_input("Ticker", "AAPL").upper()
    if st.button("Testa"):
        df = yf.download(tk, period="2y", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df['EMA'] = df['Close'].ewm(span=200, adjust=False).mean()
            df['RSI'] = calcola_rsi(df)
            cap = 1000.0
            st.metric("Capitale Finale Simulato", f"${cap:,.2f} (Esempio)")

elif menu == "Calcolatore TP/SL":
    st.header("🧮 Calcolatore")
    imp = st.number_input("Investimento ($)", value=1000)
    st.success(f"Take Profit (2%): ${imp * 1.02:.2f}")
    st.error(f"Stop Loss (1%): ${imp * 0.99:.2f}")
