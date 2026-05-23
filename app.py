import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE GOOGLE MODULI ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'passi': 'entry.1805134602'
}

# --- CARICAMENTO DATI ---
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

def recupera_meteo_automatico(data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        risposta = requests.get(url_meteo).json()
        return float(risposta['daily']['temperature_2m_max'][0])
    except:
        return 20.0

st.title("📊 Il Mio Diario della Giornata")
df_storico = pd.read_csv(URL_FOGLIO_CSV) if True else None

# --- INTERFACCIA ---
col1, col2 = st.columns(2)
with col1:
    posizione_corrente = st.text_input("📍 Ti trovi a:", value="Verona")
    temp_massima = st.number_input("Temperatura (°C)", value=recupera_meteo_automatico(datetime.date.today()))
    sonno_scelto = st.selectbox("Qualità del sonno", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia", 1, 10, 5)

with col2:
    # ATTENZIONE: le opzioni qui devono essere IDENTICHE a quelle del form
    passi_scelti = st.selectbox("Passi", ["fino a 1000", "da 1000 a 2500", "oltre 2500"])
    attivita_scelte = st.multiselect("Attività", ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])
    dolore_livello = st.slider("Dolore", 1, 10, 1)

st.write("---")
# Calcolo semplificato per brevità
valore_semaforo = st.slider("Semaforo finale", 1, 10, 5)

# --- PULSANTE REGISTRA ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    
    payload = {
        ENTRY_ID['posizione']: str(posizione_corrente),
        ENTRY_ID['temp']: str(int(round(temp_massima))),
        ENTRY_ID['sonno']: str(sonno_scelto),
        ENTRY_ID['energia']: str(int(energia)),
        ENTRY_ID['dolore']: str(int(dolore_livello)),
        ENTRY_ID['semaforo']: str(int(valore_semaforo)),
        ENTRY_ID['passi']: str(passi_scelti) 
    }
    
    payload_lista = list(payload.items())
    
    for att in attivita_scelte:
        payload_lista.append((ENTRY_ID['attivita'], str(att)))
            
    # DEBUG Visivo
    st.write("Dati inviati:", payload_lista)
            
    try:
        response = requests.post(URL_MODULO, data=payload_lista)
        if response.status_code == 200:
            st.success("🎉 Registrato!")
        else:
            st.error(f"Errore: {response.status_code}")
    except Exception as e:
        st.error(f"Errore: {e}")
