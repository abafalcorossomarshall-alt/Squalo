# 🦈 Squalo Engine - Dashboard per Analisi Tecnica Finanziaria

Piattaforma di analisi finanziaria quantitativa in tempo reale. Il software automatizza il download dei dati di borsa, elabora indicatori statistici e genera segnali operativi basati su regole matematiche rigorose.

### 🚀 Funzionalità Principali
* **Analisi Algoritmica:** Integrazione di strategie di trading strutturate: ricerca di trend rialzisti stabili tramite Media Mobile Esponenziale a 200 periodi ($EMA_{200}$) e zone di compressione sana tramite l'Indice di Forza Relativa ($RSI$).
* **Scanner Multi-Asset:** Scansione ciclica automatizzata di una watchlist di asset (Azioni USA, Crypto) con sistemi integrati di *rate-limiting* (`time.sleep`) per prevenire blocchi HTTP 429 da parte dei server Yahoo Finance.
* **Motore di Backtesting:** Modulo integrato per testare la strategia su serie storiche storiche (intervallo orario a 2 anni), calcolando il rendimento percentuale finale del capitale investito.
* **Sistema di Notifica:** Invio automatico di alert via email tramite protocollo sicuro `smtplib.SMTP_SSL` non appena i parametri di mercato soddisfano le condizioni impostate.
* **Grafici Interattivi:** Visualizzazione dinamica delle serie storiche dei prezzi e delle medie mobili tramite oggetti grafici Plotly operanti in Dark Mode.

### 🛠️ Tecnologie Utilizzate
* **Python**
* **Streamlit** (Web Dashboard)
* **yFinance** (API per il recupero asincrono di dati di mercato)
* **Pandas** (Vettorizzazione e manipolazione delle serie storiche)
* **Plotly Graph Objects** (Data Visualization)
* **Smtplib / MIMEText** (Protocolli di comunicazione mail)
