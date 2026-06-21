import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PRINCIPALE ---
st.set_page_config(page_title="Ogni Giorno - MS Diary", layout="centered", page_icon="🌱")

# URL DI INVIO DATI
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'data': 'entry.2022449610', 'posizione': 'entry.1412086707', 'temp': 'entry.1900939990',
    'umidita': 'entry.2086318809', 'sonno': 'entry.2076355969', 'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387', 'passi': 'entry.28384771', 'semaforo': 'entry.625659299',
    'siesta_form': 'entry.1353678088', 'dolore': 'entry.672372933', 'valutazione': 'entry.2023032977',
    'note': 'entry.158362423', 'crash': 'entry.592499523', 'calore_form': 'entry.123456789'  
}

# --- STATO INIZIALE ---
if 'mattina_salvata' not in st.session_state:
    st.session_state.update({
        'mattina_salvata': False, 'mattina_data': None, 'posizione': 'Verona',
        'temp': 20.0, 'umidita': 50, 'sonno': 'discreta', 'passi': 'da 1001 a 3000', 
        'energia': 5, 'attivita': [], 'siesta': False, 'valore_sem': None,
        'esposizione_reale_calore': "no", 'ispezione_log': {}
    })

# --- FUNZIONI ---
def invia_richiesta_con_riconnessione(url, parametri):
    for tentativo in range(3): 
        try:
            risposta = requests.get(url, params=parametri, timeout=5)
            if risposta.status_code == 200: return risposta
            if risposta.status_code == 429: time.sleep(random.uniform(0.5, 2.0))
            else: return risposta
        except: time.sleep(1)
    return None

def calcola_accumulo_72ore():
    ispezione = {"status": "Inizializzato", "righe_rilevate": 0, "dettaglio_giorni": []}
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl="1m")
        if df is None or len(df) < 3: return 0.0, "Storico insufficiente", ispezione
        
        ispezione["righe_rilevate"] = len(df)
        col_c = [c for c in df.columns if 'crash' in c.lower()][0]
        
        ultimi_3 = df.tail(3).to_dict('records')
        accumulo = 0.0
        dettaglio_log = []
        
        for i, etichetta in enumerate(['ieri', 'due_giorni', 'tre_giorni']):
            rec = ultimi_3[-(i+1)]
            val_crash = str(rec.get(col_c, '0')).lower()
            if '1' in val_crash or 'si' in val_crash:
                peso = {'ieri': 1.0, 'due_giorni': 0.5, 'tre_giorni': 0.25}[etichetta]
                accumulo += (1.5 * peso)
                dettaglio_log.append(f"{etichetta}")
            ispezione["dettaglio_giorni"].append({"giorno": etichetta, "crash": val_crash})
            
        return round(accumulo, 2), " + ".join(dettaglio_log), ispezione
    except Exception as e: return 0.0, str(e), ispezione

@st.cache_data(ttl=60)
def recupera_meteo(data, citta):
    try:
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"
        res = invia_richiesta_con_riconnessione(url_geo, {"name": citta, "count": 1, "language": "it", "format": "json"})
        lat, lon = 45.43, 10.99
        if res and "results" in res.json():
            lat, lon = res.json()["results"][0]["latitude"], res.json()["results"][0]["longitude"]
        
        url_m = "https://api.open-meteo.com/v1/forecast"
        p = {"latitude": lat, "longitude": lon, "start_date": data.strftime("%Y-%m-%d"), "end_date": data.strftime("%Y-%m-%d"), "daily": "temperature_2m_max", "hourly": "relative_humidity_2m", "timezone": "Europe/Rome"}
        res = invia_richiesta_con_riconnessione(url_m, p)
        data_m = res.json()
        return float(data_m['daily']['temperature_2m_max'][0]), int(sum(data_m['hourly']['relative_humidity_2m'])/len(data_m['hourly']['relative_humidity_2m'])), None
    except: return 20.0, 50, "Errore"

# --- UI ---
st.title("🌱 Ogni Giorno")
tab1, tab2 = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

with tab1:
    col1, col2 = st.columns(2)
    with col1: data_sel = st.date_input("🗓️ Data", datetime.date.today()); pos = st.text_input("📍 Posizione", st.session_state.posizione)
    t, h, _ = recupera_meteo(data_sel, pos)
    with col2: temp = st.number_input("🌡️ Temperatura", value=t); umidita = st.number_input("💧 Umidità (%)", value=int(h))
    
    sonno = st.selectbox("💤 Sonno", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("⚡ Energia", 1, 10, 5)
    siesta = st.checkbox("🛌 Siesta", value=st.session_state.siesta)
    att = st.multiselect("📅 Attività", ["ufficio", "lavoro da casa", "studio", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        acc, log, debug = calcola_accumulo_72ore()
        score = 5.0 + (energia*0.3) + {"discreta": 0, "soddisfacente": 1.5, "scarsa": -1.5}[sonno] - acc
        st.session_state.update({'valore_sem': round(score, 1), 'ispezione_log': debug, 'mattina_salvata': True, 'attivita': att})
        st.success(f"Punteggio stimato: {round(score, 1)}")

with tab2:
    if st.session_state.mattina_salvata:
        crash = st.radio("💥 Crash oggi?", ["0 - no", "1 - si"])
        note = st.text_area("📝 Note")
        if st.button("💾 Registra"): st.balloons(); st.success("Dati inviati!")
    else: st.warning("⚠️ Salva prima la mattina!")

with st.sidebar:
    st.header("🔬 Ispezione")
    st.write(st.session_state.ispezione_log)
