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

# --- NUOVA FUNZIONE METEO CON WEATHERAPI (PIÙ STABILE DI OPEN-METEO) ---
@st.cache_data(ttl=3600)
def recupera_meteo(data, nome_citta):
    # Chiave gratuita di test per WeatherAPI (stabile e veloce)
    API_KEY = "067645ccb00b41bfb90135805232110"
    try:
        d_str = data.strftime("%Y-%m-%d")
        # WeatherAPI fa geolocalizzazione e meteo in un'unica richiesta velocissima
        url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={nome_citta}&days=1&dt={d_str}&lang=it"
        
        risposta = requests.get(url, timeout=5)
        
        if risposta.status_code != 200:
            return 20.0, 50, True
            
        data_json = risposta.json()
        
        # Estraiamo la temperatura massima e l'umidità media del giorno selezionato
        val_temp = float(data_json['forecast']['forecastday'][0]['day']['maxtemp_c'])
        val_umidita = int(data_json['forecast']['forecastday'][0]['day']['avghumidity'])
        
        return val_temp, val_umidita, False
    except:
        # Se anche questo servizio fallisce, scatta il paracadute dei tuoi valori standard
        return 20.0, 50, True

# --- INTERFACCIA ACCOGLIENTE ---
st.title("🔋 La Mia Carica")
st.markdown("---")
st.markdown("Buongiorno! Prepariamoci per affrontare la giornata 😊")

tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

# ==========================================
# TAB MATTINA (Pianificazione)
# ==========================================
with tab_mattina:
    col1, col2 = st.columns(2)
    
    with col1:
        data_sel = st.date_input("🗓️ Data:", value=datetime.date.today())
        posizione_input = st.text_input("📍 Posizione:", value=st.session_state.posizione)
    
    # Esecuzione del nuovo motore meteo
    temp_api, umidita_api, usa_standard = recupera_meteo(data_sel, posizione_input)
    
    with col2:
        temp = st.number_input("🌡️ Temperatura prevista (°C):", value=temp_api)
        umidita = st.number_input("💧 Umidità media prevista (%):", value=int(umidita_api))
    
    # Segnalazione se vengono applicati i valori standard
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
            "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "
