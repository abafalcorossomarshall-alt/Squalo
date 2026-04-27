import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Squalo Dashboard 🦈", layout="wide")

# --- RECUPERO SICURO CREDENZIALI (SECRETS) ---
try:
    MIA_EMAIL_SISTEMA = st.secrets["SYSTEM_EMAIL"]
    PASSWORD_APP = st.secrets["EMAIL_PASSWORD"]
except KeyError:
    st.error("Configura 'SYSTEM_EMAIL' e 'EMAIL_PASSWORD' nei Secrets di Streamlit!")
    st.stop()

WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BTC-USD", "ETH-USD", "SOL-USD",
    "JPM", "GS", "V", "WMT", "KO", "DIS", "XOM", "LLY", "AMD"
]

# --- FUNZIONE RSI PROFESSIONALE ---
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
st.sidebar.info("Saldo Demo: $89,812")
menu = st.sidebar.selectbox("Menu Principale", 
    ["Dashboard Live", "Scanner Automatico", "Backtest Strategia", "Calcolatore TP/SL"])

# --- 1. DASHBOARD LIVE ---
if menu == "Dashboard Live":
    st.header("📈 Analisi Grafica Interattiva")
    ticker_input = st.text_input("Inserisci Ticker", "NVDA").upper()
    data = yf.download(ticker_input, period="1y", interval="1h", progress=False)
    
    if not data.empty:
        if isinstance(data.columns, pd.MultiIndex): 
            data.columns = data.columns.get_level_values(0)
        
        data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()
        data['RSI'] = calcola_rsi(data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Prezzo", line=dict(color='#4466FF')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name="EMA 200", line=dict(dash='dash', color='orange')))
        fig.update_layout(height=500, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        p_att = float(data['Close'].iloc[-1])
        r_att = float(data['RSI'].iloc[-1])
        e_att = float(data['EMA200'].iloc[-1])

        c1, c2, c3 = st.columns(3)
        c1.metric("Prezzo Attuale", f"${p_att:,.2f}")
        c2.metric("RSI (1h)", f"{r_att:.2f}")
        is_bullish = p_att > e_att
        c3.metric("Trend EMA 200", "BULLISH ✅" if is_bullish else "BEARISH ⚠️")

# --- 2. SCANNER AUTOMATICO ---
elif menu == "Scanner Automatico":
    st.header("🌊 Scanner Squalo")
    dest_mail = st.text_input("Mail per Alert", "tua@email.com")
    
    if st.button("Avvia Scansione Ora"):
        ris = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(WATCHLIST):
            try:
                progress_bar.progress((i + 1) / len(WATCHLIST))
                d = yf.download(t, period="60d", interval="1h", progress=False)
                
                if not d.empty:
                    if isinstance(d.columns, pd.MultiIndex): 
                        d.columns = d.columns.get_level_values(0)
                    
                    d_4h = d.resample('4H').last().dropna()
                    if len(d_4h) > 200:
                        d_4h['EMA200'] = d_4h['Close'].ewm(span=200, adjust=False).mean()
                        d_4h['RSI'] = calcola_rsi(d_4h)
                        
                        p = float(d_4h['Close'].iloc[-1])
                        e = float(d_4h['EMA200'].iloc[-1])
                        r = float(d_4h['RSI'].iloc[-1])
                        
                        stato = "🔥 COMPRA" if (p > e and 40 <= r <= 55) else "ATTESA"
                        if stato == "🔥 COMPRA":
                            invia_email_alert(dest_mail, t, p, r)
                        
                        ris.append({"Ticker": t, "Prezzo": round(p, 2), "RSI": round(r, 2), "Stato": stato})
                time.sleep(0.5) # Ritardo per evitare blocchi IP
            except Exception:
                continue
        
        if ris:
            st.table(pd.DataFrame(ris))
            st.success("Scansione completata!")

# --- 3. BACKTEST ---
elif menu == "Backtest Strategia":
    st.header("🧪 Backtest Personalizzabile")
    with st.expander("Parametri", expanded=True):
        ema_p = st.number_input("EMA Periodo", value=200)
        r_min = st.slider("RSI Min", 0, 100, 40)
        r_max = st.slider("RSI Max", 0, 100, 55)
    
    tk = st.text_input("Ticker", "AAPL").upper()
    if st.button("Testa"):
        df = yf.download(tk, period="2y", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            df['EMA'] = df['Close'].ewm(span=ema_p, adjust=False).mean()
            df['RSI'] = calcola_rsi(df)
            cap, pos = 1000, False
            for i in range(len(df)):
                p, r, e = df['Close'].iloc[i], df['RSI'].iloc[i], df['EMA'].iloc[i]
                if not pos and p > e and r_min <= r <= r_max:
                    p_in, pos = p, True
                elif pos and p < p_in * 0.95: # SL 5%
                    cap *= (p / p_in)
                    pos = False
            st.metric("Capitale Finale", f"${cap:,.2f}")

# --- 4. CALCOLATORE ---
elif menu == "Calcolatore TP/SL":
    st.header("🧮 Calcolatore")
    imp = st.number_input("Investimento ($)", value=1000)
    st.success(f"TP (2%): ${imp * 1.02:.2f}")
    st.error(f"SL (1%): ${imp * 0.99:.2f}")
