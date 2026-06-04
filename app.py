import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - MS Diary", layout="centered", page_icon="🔋")

# URL DEFINITIVO (Punta al formResponse del modulo ufficiale)
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

# MAPPATURA COMPLETA E CORRETTA AL 100% DEL TUO MODULO DEFINITIVO
ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'umidita': 'entry.2086318809',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'passi': 'entry.28384771',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'valutazione': 'entry.2023032977',
    'note': 'entry.158362423'
}

# --- STATO INIZIALE (Memoria dell'app) ---
if 'mattina_salvata' not in st.session_state:
    st.session_state.update({
        'mattina_salvata': False,
        'mattina_data': None, 
        'posizione': 'Verona',
        'temp': 20.0, 
        'umidita': 50, 
        'sonno': 'discreta', 
        'passi': 'da 1001 a 3000', 
        'energia': 5, 
        'attivita': [], 
        'valore_sem': None
    })

# --- FUNZIONE METEO CON OPEN-METEO (OTTIMIZZATA E SICURA) ---
@st.cache_data(ttl=3600)
def recupera_meteo(data, nome_citta):
    try:
        # 1. GEOLOCALIZZAZIONE SICURA: Gestisce correttamente gli spazi nei nomi delle città
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"
        params_geo = {
            "name": nome_citta.strip(),
            "count": 1,
            "language": "it",
            "format": "json"
        }
        risposta_geo = requests.get(url_geo, params=params_geo, timeout=5).json()
        
        # Coordinate di default (Verona) se la ricerca della città fallisce
        lat, lon = 45.43, 10.99 
        if "results" in risposta_geo and len(risposta_geo["results"]) > 0:
            lat = risposta_geo["results"][0]["latitude"]
            lon = risposta_geo["results"][0]["longitude"]
            
        # 2. GESTIONE DATA: Se la data è nel passato, cambiamo endpoint usando l'archivio storico
        d_str = data.strftime("%Y-%m-%d")
        oggi = datetime.date.today()
        
        if data < oggi:
            url_meteo = "https://archive-api.open-meteo.com/v1/archive"
        else:
            url_meteo = "https://api.open-meteo.com/v1/forecast"
            
        params_meteo = {
            "latitude": lat,
            "longitude": lon,
            "start_date": d_str,
            "end_date": d_str,
            "daily": "temperature_2m_max,relative_humidity_2m_mean",
            "timezone": "Europe/Rome"
        }
        
        # 3. RICHIESTA IN HTTPS
        risposta_meteo = requests.get(url_meteo, params=params_meteo, timeout=5)
        
        if risposta_meteo.status_code != 200:
            return 20.0, 50, True # Paracadute in caso di errore del server (es. 502)
            
        resp = risposta_meteo.json()
        val_temp = float(resp['daily']['temperature_2m_max'][0])
        val_umidita = int(resp['daily']['relative_humidity_2m_mean'][0])
        
        return val_temp, val_umidita, False
    except: 
        # Paracadute estremo in caso di totale assenza di rete
        return 20.0, 50, True

# --- INTERFACCIA UTENTE ---
st.title("🔋 La Mia Carica")
st.markdown("---")
st.markdown("Buongiorno! Prepariamoci per affrontare la giornata 😊")

# Creazione delle schede (Tab)
tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

# ==========================================
# TAB MATTINA (Pianificazione)
# ==========================================
with tab_mattina:
    col1, col2 = st.columns(2)
    
    with col1:
        data_sel = st.date_input("🗓️ Data:", value=datetime.date.today())
        posizione_input = st.text_input("📍 Posizione:", value=st.session_state.posizione)
    
    # Esecuzione del motore Open-Meteo ottimizzato
    temp_api, umidita_api, usa_standard = recupera_meteo(data_sel, posizione_input)
    
    with col2:
        temp = st.number_input("🌡️ Temperatura prevista (°C):", value=temp_api)
        umidita = st.number_input("💧 Umidità media prevista (%):", value=int(umidita_api))
    
    # Se il sistema è costretto a usare i dati standard, mostra l'avviso arancione
    if usa_standard:
        st.caption("⚠️ Dati meteo in tempo reale non disponibili. Usati valori standard (modificabili a mano).")
    
    st.markdown("---") 
    
    sonno = st.selectbox("💤 Qualità del sonno:", ["discreta", "soddisfacente", "scarsa"])
    passi = st.selectbox("🚶 Passi previsti:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
    energia = st.slider("⚡ Energia al risveglio (1-10):", 1, 10, 5)
    
    attivita = st.multiselect("📅 Attività in programma:", 
                              ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        pesi = {
            "ufficio": -0.5, "lavoro da casa": -0.2, "piccole commissioni": -0.4, 
            "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "sociale": -0.7
        }
        
        somma_att = sum([pesi[a] for a in attivita])
        if len(attivita) > 1:
            somma_att += (len(attivita) - 1) * -0.3
            
        p_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3)
        
        peso_sonno = {"discreta": 0.0,
