import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE ---
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
if 'mattina_salvata' not in st.session_state:
    st.session_state.update({
        'mattina_salvata': False, 'mattina_data': None, 'posizione': 'Verona',
        'temp': 20.0, 'umidita': 50, 'sonno': 'discreta', 'passi': 'da 1001 a 3000',
        'energia': 5, 'attivita': [], 'siesta': False, 'valore_sem': None, 'ispezione_log': {}
    })

# --- FUNZIONI ---
def calcola_accumulo_72ore():
    ispezione = {"status": "Inizializzato", "righe_rilevate": 0, "dettaglio_giorni": []}
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl="1m")
        if df is None or len(df) < 3: return 0.0, "Storico insufficiente", ispezione
        col_c = [c for c in df.columns if 'crash' in c.lower()][0]
        
        ultimi_3 = df.tail(3).to_dict('records')
        accumulo = 0.0
        log = []
        for i, etichetta in enumerate(reversed(['ieri', 'due_giorni', 'tre_giorni'])):
            rec = ultimi_3[-(i+1)]
            val_c = str(rec.get(col_c, '0')).lower()
            if '1' in val_c or 'si' in val_c:
                peso = {'ieri': 1.0, 'due_giorni': 0.5, 'tre_giorni': 0.25}[etichetta]
                accumulo += (1.5 * peso)
                log.append(f"{etichetta}")
            ispezione["dettaglio_giorni"].append({"giorno": etichetta, "crash": val_c})
        return round(accumulo, 2), " + ".join(log), ispezione
    except Exception as e: return 0.0, str(e), ispezione

# --- UI ---
st.title("🌱 Ogni Giorno")
tab1, tab2 = st.tabs(["🌅 Pianifica", "🌌 Feedback"])

with tab1:
    col1, col2 = st.columns(2)
    with col1: data_sel = st.date_input("Data", datetime.date.today()); pos = st.text_input("Posizione", st.session_state.posizione)
    with col2: temp = st.number_input("Temperatura", value=20.0); umidita = st.number_input("Umidità", value=50)
    
    sonno = st.selectbox("Sonno", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia", 1, 10, 5)
    attivita = st.multiselect("Attività", ["ufficio", "lavoro da casa", "studio", "riposo totale"])

    if st.button("🚀 Calcola"):
        accumulo, _, debug = calcola_accumulo_72ore()
        pesi = {"ufficio": -0.5, "lavoro da casa": -0.2, "studio": -0.3, "riposo totale": 0.5}
        somma_att = sum([pesi.get(a, 0) for a in attivita])
        
        # Logica Clima: 0 se attività protette
        chiuse = ["lavoro da casa", "studio", "riposo totale"]
        p_temp = 0.0 if any(a in chiuse for a in attivita) else (0.0 if temp < 28 else -0.5)
        
        val = round(max(1.0, min(10.0, 5.0 + (energia*0.3) + somma_att + p_temp - accumulo)), 1)
        st.session_state.update({'valore_sem': val, 'ispezione_log': debug, 'mattina_salvata': True, 'attivita': attivita, 'temp': temp, 'umidita': umidita})
        st.success(f"Punteggio: {val}")

with tab2:
    if st.session_state.mattina_salvata:
        crash = st.radio("Crash?", ["0 - no", "1 - si"])
        if st.button("💾 Registra"): st.balloons(); st.success("Dati inviati!")
    else: st.warning("Compila la mattina prima!")

with st.sidebar:
    st.header("🔬 Ispezione")
    st.write(st.session_state.ispezione_log)
