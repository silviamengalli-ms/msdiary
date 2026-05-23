import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE GOOGLE MODULI (MAPPATURA REALE) ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'data': 'entry.811568478',
    'temp': 'entry.170668988',
    'sonno': 'entry.1643446045',
    'energia': 'entry.1042761612',
    'passi': 'entry.111812166',
    'attivita': 'entry.1729676735',
    'dolore': 'entry.533285942',
    'semaforo': 'entry.317549883'
}

# --- CARICAMENTO DATI PER AI ---
# ⚠️ RICORDA: Sostituisci questo link con il tuo link di sola lettura in formato CSV 
# assicurandoti che il codice 'gid=' corrisponda alla NUOVA scheda creata dal modulo Google!
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

st.title("📊 Il Mio Diario della Giornata")

@st.cache_data(ttl=5)
def carica_dati(url):
    try: 
        return pd.read_csv(url)
    except: 
        return None

df_storico = carica_dati(URL_FOGLIO_CSV)

# --- INTERFACCIA UTENTE ---
st.subheader("🗓️ Inserisci i dati di oggi")
data_oggi = st.date_input("Data", datetime.date.today())

st.write("---")
col1, col2 = st.columns(2)

with col1:
    temp_massima = st.number_input("Temp. Massima (°C)", value=20.0, step=0.5)
    sonno_scelto = st.selectbox("Qualità del sonno", ["Ottima", "Buona", "Media", "Pessima"])
    energia = st.slider("Energia al risveglio", 1.0, 10.0, 7.0, 0.5)

with col2:
    passi_scelti = st.selectbox("Passi previsti", ["<5000", "5000-10000", ">10000"])
    attivita_scelta = st.selectbox("Attività", ["Lavoro", "Sport", "Riposo"])
    dolore_livello = st.slider("Livello dolore / indolenzimento", 1.0, 10.0, 1.0, 0.5)

st.write("---")
voto_reale = st.slider("Semaforo Reale (da salvare stasera)", 1.0, 10.0, 6.0, 0.5)

st.write("---")

# --- PULSANTE REGISTRA TRAMITE GOOGLE MODULI ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    payload = {
        ENTRY_ID['data']: data_oggi.strftime("%Y-%m-%d"),
        ENTRY_ID['temp']: temp_massima,
        ENTRY_ID['sonno']: sonno_scelto,
        ENTRY_ID['energia']: energia,
        ENTRY_ID['passi']: passi_scelti,
        ENTRY_ID['attivita']: attivita_scelta,
        ENTRY_ID['dolore']: int(dolore_livello),  # La scala lineare accetta solo numeri interi
        ENTRY_ID['semaforo']: voto_reale
    }
    
    try:
        response = requests.post(URL_MODULO, data=payload)
        if response.status_code == 200:
            st.balloons()
            st.success("✅ Dati inviati al Modulo e registrati sul Foglio Google!")
        else:
            st.error("❌ Errore nell'invio. Verifica la connessione dell'app.")
    except:
        st.error("❌ Errore di connessione con il server di Google.")

# --- SEZIONE PREDIZIONE AI ---
if st.button("🔮 Calcola Predizione AI"):
    st.info("Funzione AI attiva. Calcolo in corso basato sullo storico...")
    # Qui re-inseriremo la logica predittiva non appena verifichiamo che il salvataggio funziona alla perfezione
