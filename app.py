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
            if risposta.status_code == 200: return risposta 
            elif risposta.status_code == 429:
                time.sleep(random.uniform(0.5, 2.0))
                continue
            else: return risposta
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
