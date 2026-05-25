import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="MS Diary - Predizione", layout="centered")

# --- COSTANTI ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"
ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387', # ID per le checkbox
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'passi': 'entry.28384771',
    'note': 'entry.158362423'
}

PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.1, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.4, "riposo totale": 0.5, "sociale": -0.7
}

# --- INTERFACCIA ---
st.title("📊 Registrazione Giornata")
data_sel = st.date_input("Data:", value=datetime.date.today(), format="DD/MM/YYYY")
attivita = st.multiselect("Attività (seleziona più opzioni):", list(PESI_ATTIVITA.keys()))
note_input = st.text_area("Note:")

# --- INVIO ---
if st.button("💾 Registra Giornata"):
    # Creiamo una lista di tuple "piatta"
    dati = [
        (ENTRY_ID['data'], data_sel.strftime("%Y-%m-%d")),
        (ENTRY_ID['note'], note_input)
    ]
    
    # AGGIUNGIAMO LE ATTIVITA' COME CHIAVI RIPETUTE
    # Questo è l'unico modo per Google Forms di accettare checkbox multiple
    for item in attivita:
        dati.append((ENTRY_ID['attivita'], item))
    
    try:
        # Invio diretto della lista di tuple
        r = requests.post(URL_MODULO, data=dati)
        if r.status_code == 200:
            st.success("✅ Inviato correttamente!")
        else:
            st.error(f"❌ Errore {r.status_code}")
            st.write("Dati inviati (verifica che l'ID attività compaia più volte):", dati)
    except Exception as e:
        st.error(f"⚠️ Errore: {e}")
