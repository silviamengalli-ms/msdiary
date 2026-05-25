import streamlit as st
import datetime
import requests

st.set_page_config(page_title="MS Diary - Debug", layout="centered")

# --- ID CAMPI ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"
ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'passi': 'entry.28384771',
    'note': 'entry.158362423'
}

# --- UI SEMPLIFICATA PER TEST ---
st.title("🔧 Debug Invio Dati")
data_sel = st.date_input("Data", value=datetime.date.today())
note_val = st.text_input("Nota", value="Test invio")

if st.button("🚀 INVIA TEST"):
    # Prepariamo solo i dati essenziali
    dati = [
        (ENTRY_ID['data'], data_sel.strftime("%Y-%m-%d")), 
        (ENTRY_ID['note'], note_val)
    ]
    
    try:
        r = requests.post(URL_MODULO, data=dati)
        if r.status_code == 200:
            st.success("✅ Successo!")
        else:
            st.error(f"❌ Errore {r.status_code}")
            st.write("Dati inviati:", dati)
            st.write("Verifica se il link URL_MODULO è corretto e se il modulo accetta risposte.")
    except Exception as e:
        st.error(f"Errore: {e}")
