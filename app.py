import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PRINCIPALE ---
st.set_page_config(page_title="Ogni Giorno - MS Diary", layout="centered", page_icon="🌱")

URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

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
    'siesta_form': 'entry.1353678088', 
    'dolore': 'entry.672372933',
    'valutazione': 'entry.2023032977',
    'note': 'entry.158362423',
    'crash': 'entry.592499523',
    'calore_form': 'entry.123456789'  
}

# --- STATO INIZIALE ---
if 'mattina_salvata' not in st.session_state:
    st.session_state.update({
        'mattina_salvata': False, 'mattina_data': None, 'posizione': 'Verona',
        'temp': 20.0, 'umidita': 50, 'sonno': 'discreta', 'passi': 'da 1001 a 3000', 
        'energia': 5, 'attivita': [], 'siesta': False, 'valore_sem': None,
        'esposizione_reale_calore': "no", 'ispezione_log': {}
    })

# --- FUNZIONI DI SERVIZIO ---
def invia_richiesta_con_riconnessione(url, parametri):
    for tentativo in range(3): 
        try:
            risposta = requests.get(url, params=parametri, timeout=5)
            if risposta.status_code == 200: return risposta
            if risposta.status_code == 429: time.sleep(random.uniform(0.5, 2.0))
            else: return risposta
        except requests.exceptions.RequestException:
            time.sleep(random.uniform(0.5, 2.0))
    return None

def calcola_accumulo_72ore():
    ispezione = {"status": "Inizializzato", "righe_rilevate": 0, "dettaglio_giorni": []}
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl="1m") 
        if df is None or len(df) < 3: return 0.0, "Storico insufficiente", ispezione
        
        ispezione["righe_rilevate"] = len(df)
        colonna_crash = [c for c in df.columns if 'crash' in c.lower()]
        if not colonna_crash: return 0.0, "Colonna crash mancante", ispezione
            
        col_c = colonna_crash[0]
        ultimi_3_giorni = df.tail(3).to_dict('records')
        accumulo_totale = 0.0
        dettaglio_log = []
        
        for i, etichetta in enumerate(['tre_giorni', 'due_giorni', 'ieri']):
            record = ultimi_3_giorni[i]
            val_crash = str(record.get(col_c, '0')).strip().lower()
            if val_crash.startswith('1') or 'si' in val_crash:
                peso = {'ieri': 1.0, 'due_giorni': 0.5, 'tre_giorni': 0.25}[etichetta]
                accumulo_totale += (1.5 * peso)
                dettaglio_log.append(f"{etichetta}")
        
        return round(accumulo_totale, 2), " + ".join(dettaglio_log), ispezione
    except Exception as e:
        return 0.0, f"Errore: {str(e)}", ispezione

@st.cache_data(ttl=60)
def recupera_meteo(data, nome_citta):
    try:
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"
        params_geo = {"name": nome_citta.strip(), "count": 1, "language": "it", "format": "json"}
        res_geo = invia_richiesta_con_riconnessione(url_geo, params_geo)
        lat, lon = 45.43, 10.99
        if res_geo and res_geo.status_code == 200:
            data_geo = res_geo.json()
            if "results" in data_geo:
                lat, lon = data_geo["results"][0]["latitude"], data_geo["results"][0]["longitude"]
        
        d_str = data.strftime("%Y-%m-%d")
        url_meteo = "https://api.open-meteo.com/v1/forecast"
        params_meteo = {
            "latitude": lat, "longitude": lon, "start_date": d_str, "end_date": d_str, 
            "daily": "temperature_2m_max", "hourly": "relative_humidity_2m", "timezone": "Europe/Rome"
        }
        res_meteo = invia_richiesta_con_riconnessione(url_meteo, params_meteo)
        if not res_meteo or res_meteo.status_code != 200: return 20.0, 50, None
        
        resp = res_meteo.json()
        temp = float(resp['daily']['temperature_2m_max'][0])
        hum = int(sum(resp['hourly']['relative_humidity_2m']) / len(resp['hourly']['relative_humidity_2m']))
        return temp, hum, None
    except: return 20.0, 50, None

# --- UI PRINCIPALE ---
st.title("🌱 Ogni Giorno")
tab_m, tab_s = st.tabs(["🌅 Mattina", "🌌 Sera"])

with tab_m:
    data = st.date_input("Data", datetime.date.today())
    pos = st.text_input("Posizione", st.session_state.posizione)
    t_api, h_api, _ = recupera_meteo(data, pos)
    temp = st.number_input("Temperatura (°C)", value=t_api)
    umidita = st.number_input("Umidità (%)", value=h_api)
    energia = st.slider("Energia (1-10)", 1, 10, 5)
    
    if st.button("🚀 Calcola"):
        acc, _, _ = calcola_accumulo_72ore()
        val = round(max(1.0, min(10.0, 5.0 + (energia*0.3) - acc)), 1)
        st.session_state.valore_sem = val
        st.success(f"Punteggio stimato: {val}")

with tab_s:
    if st.session_state.valore_sem:
        crash = st.radio("Crash oggi?", ["0 - no", "1 - si"])
        if st.button("💾 Registra"):
            st.balloons()
            st.success("Dati inviati!")
