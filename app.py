import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - Diario Energetico", layout="centered")

URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSdtqnrzl71uqLgb1-wY5yw3R2vo7m8-nSwGgNf7ZtbrchqlYw/formResponse"

ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'passi': 'entry.28384771',
    'note': 'entry.158362423',
    'valutazione_predizione': 'entry.375319797'
}

# --- PESI RICALIBRATI ---
PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.3}
PESI_ATTIVITA = {
    "ufficio": -0.3, 
    "lavoro da casa": -0.1, 
    "piccole commissioni": -0.3, 
    "visita": -0.3, 
    "fisioterapia": -0.3, 
    "riposo totale": 0.5, 
    "sociale": -0.5
}

# --- LOGICA METEO ---
@st.cache_data(ttl=3600)
def recupera_meteo(data):
    try:
        data_str = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0])
    except: 
        return 20.0

# --- INTERFACCIA ---
st.header("🔋 La Mia Carica")

tab_mattina, tab_sera = st.tabs(["🌅 Mattina", "🌌 Sera"])

with tab_mattina:
    data_sel = st.date_input("Seleziona la data di oggi:", value=datetime.date.today(), format="DD-MM-YYYY")
    temp_prevista = recupera_meteo(data_sel)
    
    col1, col2 = st.columns(2)
    with col1:
        temp = st.slider("Temperatura prevista oggi (°C):", -5.0, 45.0, float(temp_prevista), 0.5)
        sonno = st.selectbox("Qualità del sonno:", list(PESI_SONNO.keys()))
    with col2:
        passi = st.selectbox("Passi previsti:", list(PESI_PASSI.keys()))
        energia = st.slider("Energia al risveglio (1-10):", 1, 10, 5)
        
    attivita = st.multiselect("Attività in programma:", list(PESI_ATTIVITA.keys()))

    # --- CALCOLO RICALIBRATO ---
    somma_pesi_attivita = sum([PESI_ATTIVITA[a] for a in attivita])
    
    if temp <= 28.0:
        peso_temperatura = 0.0
    elif 28.0 < temp <= 30.0:
        peso_temperatura = -0.5
    else:
        peso_temperatura = -1.0 - ((temp - 30.0) * 0.1)
    
    # Formula: Base 5.0 + Energia (0.3) + Fattori
    score = 5.0 + (energia * 0.3) + PESI_SONNO[sonno] + PESI_PASSI[passi] + somma_pesi_attivita + peso_temperatura
    valore_sem = round(max(1.0, min(10.0, score)), 1)
    st.session_state.valore_sem = valore_sem

    # Visualizzazione Bollino
    if valore_sem <= 4.5:
        st.error(f"🔴 BOLLINO ROSSO: {valore_sem}")
    elif valore_sem <= 7.0:
