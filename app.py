import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE E PESI ---
st.set_page_config(page_title="La Mia Carica", layout="centered")

PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.3}
PESI_ATTIVITA = {
    "ufficio": -0.5, # Resi leggermente più pesanti per far sentire la differenza
    "lavoro da casa": -0.2, 
    "piccole commissioni": -0.4, 
    "visita": -0.5, 
    "fisioterapia": -0.5, 
    "riposo totale": 0.5, 
    "sociale": -0.7
}

# --- INTERFACCIA E CALCOLO ---
with st.container():
    # ... (input data, temp, sonno, energia) ...
    attivita = st.multiselect("Attività in programma:", list(PESI_ATTIVITA.keys()))

    # CALCOLO AGGRESSIVO
    pesi_selezionati = [PESI_ATTIVITA[a] for a in attivita]
    somma_pesi_attivita = sum(pesi_selezionati)
    
    # Penalità cumulativa: più attività fai, più il peso aumenta
    if len(attivita) > 1:
        somma_pesi_attivita += (len(attivita) - 1) * -0.3
    
    # Penalità meteo (già ricalibrata)
    if temp < 28.0:
        peso_temperatura = 0.0
    else:
        peso_temperatura = -0.5 - ((temp - 28.0) * 0.3)
    
    # Nuova formula con attività più pesanti
    score = 5.0 + (energia * 0.3) + PESI_SONNO[sonno] + PESI_PASSI[passi] + somma_pesi_attivita + peso_temperatura
    valore_sem = round(max(1.0, min(10.0, score)), 1)
