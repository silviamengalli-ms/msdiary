import streamlit as st
import datetime
import requests

# 1. Configurazione base (sempre per prima)
st.set_page_config(page_title="MS Diary", layout="centered")

# 2. Costanti
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

# 3. Interfaccia
st.title("📊 Diario MS")

# (Tutte le tue input fields vanno qui, indentate correttamente)
data = st.date_input("Data", value=datetime.date.today())
pos = st.text_input("Luogo", value="Verona")
sonno = st.selectbox("Sonno", ["discreta", "soddisfacente", "scarsa"])
# ... (inserisci qui gli altri input) ...

# 4. Bottone (Gestito correttamente)
if st.button("💾 Registra"):
    # Questo blocco viene eseguito solo al click
    payload = {
        ENTRY_ID['data']: data.strftime("%d/%m/%Y"),
        ENTRY_ID['posizione']: pos,
        # ... aggiungi qui il resto ...
    }
    
    try:
        response = requests.post(URL_MODULO, data=payload)
        if response.status_code == 200:
            st.success("Inviato!")
        else:
            st.error("Errore invio")
    except Exception as e:
        st.error(f"Errore: {e}")
