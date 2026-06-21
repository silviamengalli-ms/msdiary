import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PRINCIPALE ---
st.set_page_config(page_title="Ogni Giorno - MS Diary", layout="centered", page_icon="🌱")

# URL DI INVIO DATI PRINCIPALE (formResponse)
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

# MAPPATURA INPUT GOOGLE MODULI AGGIORNATA (MAIN)
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
stato_iniziale = {
    'mattina_salvata': False,
    'mattina_data': None, 
    'posizione': 'Verona',
    'temp': 20.0, 
    'umidita': 50, 
    'sonno': 'discreta', 
    'passi': 'da 1001 a 3000', 
    'energia': 5, 
    'attivita': [], 
    'siesta': False,  
    'valore_sem': None,
    'esposizione_reale_calore': "no",
    'ispezione_log': {}
}

for chiave, valore in stato_iniziale.items():
    if chiave not in st.session_state:
        st.session_state[chiave] = valore

# --- FUNZIONE RE-TRY LOGIC ---
def invia_richiesta_con_riconnessione(url, parametri):
    for tentativo in range(3): 
        try:
            risposta = requests.get(url, params=parametri, timeout=5)
            if risposta.status_code == 200:
                return risposta 
            elif risposta.status_code == 429:
                time.sleep(random.uniform(0.5, 2.0))
                continue
            else:
                return risposta
        except requests.exceptions.RequestException:
            time.sleep(random.uniform(0.5, 2.0))
    return None

# --- FUNZIONE INTERNA: CALCOLO DIRETTO DELLE 72 ORE (ACCUMULO) ---
def calcola_accumulo_72ore():
    ispezione = {
        "status": "Inizializzato",
        "righe_rilevate": 0,
        "dettaglio_giorni": []
    }
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl="1m") 
        
        if df is None or len(df) < 3:
            ispezione["status"] = "Storico insufficiente"
            return 0.0, "Storico insufficiente nel database", ispezione
        
        ispezione["righe_rilevate"] = len(df)
        colonna_crash = [c for c in df.columns if 'crash' in c.lower()]
        colonna_match = [c for c in df.columns if 'valutazione' in c.lower() or 'riscontro' in c.lower()]
        
        if not colonna_crash:
            ispezione["status"] = "Colonna crash mancante"
            return 0.0, "Nessun accumulo attivo (Manca colonna Crash)", ispezione
            
        col_c = colonna_crash[0]
        col_m = colonna_match[0] if colonna_match else None
        
        ultimi_3_giorni = df.tail(3).to_dict('records')
        giorni_etichette = ['ieri', 'due_giorni', 'tre_giorni']
        pesi_temporali = {'ieri': 1.0, 'due_giorni': 0.5, 'tre_giorni': 0.25}
        
        accumulo_totale = 0.0
        dettaglio_log = []
        
        for i, etichetta in enumerate(reversed(giorni_etichette)):
            record = ultimi_3_giorni[i]  
            val_crash = str(record.get(col_c, '0')).strip().lower()
            val_match = str(record.get(col_m, '')).strip() if col_m else "N/D"
            
            info_giorno = {
                "giorno": etichetta,
                "crash_rilevato": val_crash,
                "riscontro_serale": val_match,
                "peso_temporale": pesi_temporali[etichetta],
                "penalita_applicata": 0.0
            }
            
            if val_crash.startswith('1') or 'si' in val_crash or 'sì' in val_crash:
                impatto = 1.5 * pesi_temporali[etichetta]
                if val_match == "Underestimated":
                    impatto *= 1.5
                    info_giorno["moltiplicatore_protezione"] = "Attivo (x1.5)"
                
                accumulo_totale += impatto
                info_giorno["penalita_applicata"] = round(impatto, 2)
                dettaglio_log.append(f"{etichetta} (-{round(impatto, 2)})")
                
            ispezione["dettaglio_giorni"].append(info_giorno)
            
        stringa_report = " + ".join(dettaglio_log) if dettaglio_log else "Nessun sovraccarico rilevato."
        ispezione["status"] = "Calcolo completato con successo"
        return round(accumulo_totale, 2), stringa_report, ispezione

    except Exception as e:
        ispezione["status"] = f"Errore: {str(e)}"
        return 0.0, "Errore allineamento", ispezione

# --- FUNZIONE METEO ---
@st.cache_data(ttl=60)
def recupera_meteo(data, nome_citta):
    try:
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"
        params_geo = {"name": nome_citta.strip(), "count": 1, "language": "it", "format": "json"}
        risposta_geo = invia_richiesta_con_riconnessione(url_geo, params_geo)
        
        if not risposta_geo or risposta_geo.status_code != 200:
            return 20.0, 50, "Errore di rete"
            
        data_geo = risposta_geo.json()
        lat, lon = 45.43, 10.99
        
        if "results" in data_geo and len(data_geo["results"]) > 0:
            lat = data_geo["results"][0]["latitude"]
            lon = data_geo["results"][0]["longitude"]
        else:
            return 20.0, 50, "Città non trovata."
            
        d_str = data.strftime("%Y-%m-%d")
        url_meteo = "https://api.open-meteo.com/v1/forecast"
        params_meteo = {
            "latitude": lat, 
            "longitude": lon, 
            "start_
