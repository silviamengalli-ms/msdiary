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
    'data': 'entry.2022449610', 'posizione': 'entry.1412086707', 'temp': 'entry.1900939990',
    'umidita': 'entry.2086318809', 'sonno': 'entry.2076355969', 'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387', 'passi': 'entry.28384771', 'semaforo': 'entry.625659299',
    'siesta_form': 'entry.1353678088', 'dolore': 'entry.672372933', 'valutazione': 'entry.2023032977',
    'note': 'entry.158362423', 'crash': 'entry.592499523'
}

# --- STATO INIZIALE ---
stato_iniziale = {
    'mattina_salvata': False, 'mattina_data': None, 'posizione': 'Verona',
    'temp': 20.0, 'umidita': 50, 'sonno': 'discreta', 'passi': 'da 1001 a 3000', 
    'energia': 5, 'attivita': [], 'siesta': False, 'valore_sem': None, 'ispezione_log': {}
}
for k, v in stato_iniziale.items():
    if k not in st.session_state: st.session_state[k] = v

# --- FUNZIONI ---
def invia_richiesta_con_riconnessione(url, parametri):
    for _ in range(3):
        try:
            r = requests.get(url, params=parametri, timeout=5)
            if r.status_code == 200: return r
            time.sleep(1)
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
        col_m = next((c for c in df.columns if 'valutazione' in c.lower() or 'riscontro' in c.lower()), None)
        
        ultimi_3 = df.tail(3).to_dict('records')
        accumulo = 0.0
        log = []
        for i, etichetta in enumerate(reversed(['ieri', 'due_giorni', 'tre_giorni'])):
            rec = ultimi_3[-(i+1)]
            val_c = str(rec.get(col_c, '0')).lower()
            val_m = str(rec.get(col_m, '')).strip()
            peso = {'ieri': 1.0, 'due_giorni': 0.5, 'tre_giorni': 0.25}[etichetta]
            
            if '1' in val_c or 'si' in val_c:
                imp = 1.5 * peso
                if val_m == "Underestimated": imp *= 1.5
                accumulo += imp
                log.append(f"{etichetta} (-{round(imp, 2)})")
            ispezione["dettaglio_giorni"].append({"giorno": etichetta, "crash_
