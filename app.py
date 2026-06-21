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
