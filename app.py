import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE GOOGLE MODULI ---
# ⚠️ SOSTITUISCI QUESTO LINK CON IL LINK DEL TUO MODULO (Deve finire con /formResponse)
URL_MODULO = "https://docs.google.com/forms/d/e/IL_TUO_ID_LUNGO/formResponse"

# ⚠️ DA COMPLETARE: Sostituisci i numeri qui sotto con i tuoi entry.XXXXX
ENTRY_ID = {
    'data': 'entry.11111111',
    'temp': 'entry.22222222',
    'sonno': 'entry.33333333',
    'energia': 'entry.44444444',
    'passi': 'entry.55555555',
    'attivita': 'entry.66666666',
    'dolore': 'entry.88888888',  # <-- Nuovo parametro aggiunto qui
    'semaforo': 'entry.77777777'
}

# --- CARICAMENTO DATI PER AI ---
# ⚠️ Aggiorna il link inserendo il GID della nuova scheda delle risposte del modulo
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=IL_GID_DEL_FOGLIO_RISPOSTE"

st.title("📊 Il Mio Diario della Giornata")

@st.cache_data(ttl=5)
def carica_dati(url):
    try: return pd.read_csv(url)
    except: return None

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
    dolore_livello = st.slider("Livello dolore / indolenzimento", 1.0, 10.0, 1.0, 0.5) # <-- Nuovo Slider applicato

st.write("---")
voto_reale = st.slider("Semaforo Reale (da salvare stasera)", 1.0, 10.0, 6.0, 0.5)

st.write("---")

# --- PULSANTE REGISTRA (SCRIVE SUL FOGLIO) ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    payload = {
        ENTRY_ID['data']: data_oggi.strftime("%Y-%m-%d"),
        ENTRY_ID['temp']: temp_massima,
        ENTRY_ID['sonno']: sonno_scelto,
        ENTRY_ID['energia']: energia,
        ENTRY_ID['passi']: passi_scelti,
        ENTRY_ID['attivita']: attivita_scelta,
        ENTRY_ID['dolore']: dolore_livello,
        ENTRY_ID['semaforo']: voto_reale
    }
    
    try:
        response = requests.post(URL_MODULO, data=payload)
        if response.status_code == 200:
            st.balloons()
            st.success("✅ Dati inviati al Modulo e registrati sul Foglio Google!")
        else:
            st.error("❌ Errore nell'invio. Verifica gli ENTRY_ID e il link del modulo.")
    except:
        st.error("❌ Errore di connessione.")

# --- SEZIONE PREDIZIONE AI ---
if st.button("🔮 Calcola Predizione AI"):
    st.info("Funzione AI in ottimizzazione con il nuovo parametro...")
    # Qui si attiverà il modello matematico aggiornato
