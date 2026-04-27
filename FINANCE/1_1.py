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

# Watchlist separata per gestire le diverse API
CRYPTO_LIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
STOCKS_LIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD"]

# --- FUNZIONI TECNICHE ---

def get_binance_data(symbol, interval='4h', limit=300):
    """Recupera dati da Binance API (Senza blocchi IP severi)"""
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
    corpo = f"Segnale rilevato per {ticker}!\nPrezzo: {prezzo:.2f}\nRSI: {rsi:.2f}\nLogica: Trend Rialzista sopra EMA 200."
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
st.sidebar.info("API ibrida: Binance + Yahoo")
menu = st.sidebar.selectbox("Menu Principale", ["Dashboard Live", "Scanner Automatico", "Calcolatore TP/SL"])

# --- 1. DASHBOARD LIVE ---
if menu == "Dashboard Live":
    st.header("📈 Analisi Grafica")
    tk = st.text_input("Inserisci Ticker (es. BTCUSDT o NVDA)", "BTCUSDT").upper()
    
    # Se è una crypto di Binance
    if "USDT" in tk:
        df = get_binance_data(tk)
    else:
        df = yf.download(tk, period="1y", interval="1h", progress=False)
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

    if df is None or df.empty:
        st.error("Dati non disponibili. Controlla il Ticker o riprova.")
    else:
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['RSI'] = calcola_rsi(df)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Prezzo", line=dict(color='#4466FF')))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name="EMA 200", line=dict(dash='dash', color='orange')))
        fig.update_layout(height=500, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        p_att, r_att, e_att = df['Close'].iloc[-1], df['RSI'].iloc[-1], df['EMA200'].iloc[-1]
        
        # Descrizioni Dinamiche
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🧐 Analisi Trend")
            if p_att > e_att:
                st.success(f"BULLISH: Prezzo (${p_att:.2f}) sopra EMA 200. Trend positivo.")
            else:
                st.error(f"BEARISH: Prezzo (${p_att:.2f}) sotto EMA 200. Trend negativo.")
        with col2:
            st.subheader("📊 Analisi RSI")
            st.info(f"RSI attuale: {r_att:.2f}. " + ("Zona Ricarica (Ottimale)" if 40 <= r_att <= 55 else "Zona Neutra/Estrema"))

# --- 2. SCANNER AUTOMATICO ---
elif menu == "Scanner Automatico":
    st.header("🌊 Scanner Squalo (Binance + Yahoo)")
    dest_mail = st.text_input("Mail per Alert", "tua@email.com")
    
    if st.button("Avvia Scansione"):
        ris = []
        bar = st.progress(0)
        totale = len(CRYPTO_LIST) + len(STOCKS_LIST)
        
        # --- SCANSIONE CRYPTO (Binance - Veloce e Sicura) ---
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

        # --- SCANSIONE STOCKS (Yahoo - Con pause per evitare blocchi) ---
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
                time.sleep(2) # Pausa necessaria per Yahoo
            except: continue

        if ris: st.table(pd.DataFrame(ris))
        st.success("Scansione terminata!")

# --- 4. CALCOLATORE ---
elif menu == "Calcolatore TP/SL":
    st.header("🧮 Calcolatore")
    imp = st.number_input("Investimento ($)", value=1000)
    st.write(f"🟢 Take Profit (2%): **${imp * 1.02:.2f}**")
    st.write(f"🔴 Stop Loss (1%): **${imp * 0.99:.2f}**")
