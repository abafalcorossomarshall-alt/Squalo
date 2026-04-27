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

# --- COSTANTI ---
MIA_EMAIL_SISTEMA = "abafalcorosso.marshall@gmail.com"
PASSWORD_APP = "kgjk rejz isok gdad"

WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BTC-USD", "ETH-USD", "SOL-USD",
    "JPM", "GS", "V", "WMT", "KO", "DIS", "XOM", "LLY", "AMD"
]

# --- FUNZIONI CORE ---
def calcola_rsi(data, window=14):
    # Calcola il delta (differenza di prezzo tra chiusure consecutive)
    delta = data['Close'].diff()
    
    # Separa guadagni (up) e perdite (down)
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Usa la Media Mobile Esponenziale (metodo di Wilder/Standard professionale)
    ma_up = up.ewm(com=window - 1, adjust=False).mean()
    ma_down = down.ewm(com=window - 1, adjust=False).mean()
    
    # Calcola il Relative Strength (RS)
    rs = ma_up / ma_down.replace(0, 0.00001)
    
    # Ritorna l'RSI finale
    return 100 - (100 / (1 + rs))

def invia_email_alert(destinatario, ticker, prezzo, rsi):
    oggetto = f"🦈 SQUALO ALERT: {ticker} a {prezzo:.2f}"
    corpo = f"Segnale rilevato per {ticker}!\nPrezzo: {prezzo:.2f}\nRSI: {rsi:.2f}\nLogica: Prezzo sopra EMA200 e RSI in zona di ricarica."
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

# --- SIDEBAR NAVIGAZIONE ---
st.sidebar.title("🦈 Squalo Engine")
st.sidebar.info("Saldo Demo: $89,812")
menu = st.sidebar.selectbox("Menu Principale", 
    ["Dashboard Live", "Scanner Automatico", "Backtest Strategia", "Calcolatore TP/SL"])

# --- 1. DASHBOARD LIVE ---
if menu == "Dashboard Live":
    st.header("📈 Analisi Grafica Interattiva")
    ticker_input = st.text_input("Inserisci Ticker", "BTC-USD").upper()
    data = yf.download(ticker_input, period="1y", interval="1h", progress=False)
    
    if not data.empty:
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()
        data['RSI'] = calcola_rsi(data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Prezzo", line=dict(color='#4466FF')))
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name="EMA 200", line=dict(dash='dash', color='orange')))
        fig.update_layout(height=500, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        prezzo_attuale = float(data['Close'].iloc[-1])
        rsi_attuale = float(data['RSI'].iloc[-1])
        ema_attuale = float(data['EMA200'].iloc[-1])

        c1, c2, c3 = st.columns(3)
        c1.metric("Prezzo Attuale", f"${prezzo_attuale:,.2f}")
        c2.metric("RSI (1h)", f"{rsi_attuale:.2f}")
        is_bullish = prezzo_attuale > ema_attuale
        c3.metric("Trend EMA 200", "BULLISH ✅" if is_bullish else "BEARISH ⚠️")

        st.markdown("---")
        col_desc1, col_desc2 = st.columns(2)
        with col_desc1:
            st.subheader("🧐 Logica del Trend")
            if is_bullish:
                st.success(f"**TREND RIALZISTA**: Il prezzo è sopra la EMA 200 (${ema_attuale:,.2f}). Fase di forza strutturale.")
            else:
                st.error(f"**TREND RIBASSISTA**: Il prezzo è sotto la EMA 200 (${ema_attuale:,.2f}). Fase di debolezza.")
        
        with col_desc2:
            st.subheader("📊 Analisi RSI")
            if 40 <= rsi_attuale <= 55:
                st.info(f"**ZONA SANA ({rsi_attuale:.2f})**: Il prezzo ha rifiatato ed è pronto a ripartire.")
            elif rsi_attuale > 70:
                st.warning(f"**IPERCOMPRATO ({rsi_attuale:.2f})**: Il prezzo è salito troppo velocemente, rischio storno elevato.")
            elif rsi_attuale < 30:
                st.warning(f"**IPERVENDUTO ({rsi_attuale:.2f})**: Il prezzo è sceso troppo velocemente.")

# --- 2. SCANNER AUTOMATICO (LOOP) ---
elif menu == "Scanner Automatico":
    st.header("🌊 Scanner Squalo in Loop")
    
    email_dest = st.text_input("Inserisci l'email per ricevere gli alert", "tuaemail@esempio.com")
    intervallo = st.slider("Frequenza controllo (ore)", 1, 12, 4)
    run_scanner = st.checkbox("Avvia Scanner")
    
    log_area = st.empty()
    status_area = st.empty()

    if run_scanner:
        while True:
            risultati = []
            ora_attuale = datetime.now().strftime("%H:%M:%S")
            status_area.write(f"🔄 Scansione in corso... (Ultimo check: {ora_attuale})")
            
            for t in WATCHLIST:
                try:
                    d = yf.download(t, period="60d", interval="1h", progress=False)
                    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
                    d_4h = d.resample('4H').last().dropna()
                    d_4h['EMA200'] = d_4h['Close'].ewm(span=200, adjust=False).mean()
                    d_4h['RSI'] = calcola_rsi(d_4h)
                    
                    p, e, r = d_4h['Close'].iloc[-1], d_4h['EMA200'].iloc[-1], d_4h['RSI'].iloc[-1]
                    
                    if p > e and 40 <= r <= 55:
                        giudizio = "🔥 COMPRA"
                        invia_email_alert(email_dest, t, p, r)
                    else:
                        giudizio = "ATTESA"
                    
                    risultati.append({"Ticker": t, "Prezzo": round(p, 2), "RSI": round(r, 2), "Stato": giudizio})
                except: continue
            
            log_area.table(pd.DataFrame(risultati))
            time.sleep(intervallo * 3600)
            st.rerun()

# --- 3. BACKTEST STRATEGIA ---
elif menu == "Backtest Strategia":
    st.header("🧪 Configura e Testa la tua Strategia")
    
    st.markdown("""> **Strategia Squalo**: Si entra quando il trend di lungo termine è positivo (Prezzo > Media Mobile) 
    e l'oscillatore indica una ricarica di forza (RSI in zona pullback).""")
    
    with st.expander("Parametri Strategia", expanded=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        ema_period = col_p1.number_input("Periodo Media Mobile (EMA)", value=200)
        rsi_min = col_p2.slider("RSI Minimo (Entrata)", 0, 100, 40)
        rsi_max = col_p3.slider("RSI Massimo (Entrata)", 0, 100, 55)
        trail_stop = st.slider("Trailing Stop (%)", 1.0, 15.0, 5.0) / 100

    tk = st.text_input("Ticker da testare", "AAPL").upper()
    
    if st.button("Esegui Backtest"):
        df = yf.download(tk, period="2y", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df['EMA'] = df['Close'].ewm(span=ema_period, adjust=False).mean()
            df['RSI'] = calcola_rsi(df)
            df.dropna(inplace=True)
            
            capitale, pos_aperta, vittorie, perdite = 1000, False, 0, 0
            
            for i in range(len(df)):
                p, r, e = df['Close'].iloc[i], df['RSI'].iloc[i], df['EMA'].iloc[i]
                if not pos_aperta and p > e and rsi_min <= r <= rsi_max:
                    p_in, stop, pos_aperta = p, p * (1 - trail_stop), True
                elif pos_aperta:
                    stop = max(stop, p * (1 - trail_stop))
                    if p <= stop:
                        capitale *= (p / p_in); capitale -= 1 # -1 di commissione simulata
                        if p > p_in: vittorie += 1
                        else: perdite += 1
                        pos_aperta = False
            
            st.subheader(f"Risultato Finale: ${capitale:,.2f}")
            win_rate = (vittorie/(vittorie+perdite+0.001)*100)
            st.write(f"Win Rate: {win_rate:.2f}% | Trade Totali: {vittorie + perdite}")

# --- 4. CALCOLATORE TP/SL ---
elif menu == "Calcolatore TP/SL":
    st.header("🧮 Money Management")
    importo = st.number_input("Quanto vuoi investire?", value=1000)
    c_tp, c_sl = st.columns(2)
    c_tp.success(f"TAKE PROFIT (2%): ${importo * 0.02:.2f}")
    c_sl.error(f"STOP LOSS (1%): ${importo * 0.01:.2f}")