import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="MS Diary - Definitivo", layout="centered")

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

PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.1, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.4, "riposo totale": 0.5, "sociale": -0.7
}

# --- INTERFACCIA ---
st.title("📊 Diario MS")
data_sel = st.date_input("Data:", value=datetime.date.today())
posizione = st.text_input("Luogo:", value="Verona")
sonno = st.selectbox("Sonno:", ["discreta", "soddisfacente", "scarsa"])
energia = st.slider("Energia (1-10):", 1, 10, 5)
passi = st.selectbox("Passi:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
attivita = st.multiselect("Attività:", list(PESI_ATTIVITA.keys()))
dolore = st.slider("Dolore:", 1, 10, 1)
note_input = st.text_area("Note:")
feedback = st.selectbox("Feedback:", ["#Match", "#Overestimate", "#Underestimate"])

# --- INVIO ---
if st.button("💾 Registra Giornata"):
    # Costruiamo la lista di dati come tuple (chiave, valore)
    # Fondamentale: inviamo ogni attività come voce separata con lo stesso ENTRY ID
    payload = [
        (ENTRY_ID['data'], data_sel.strftime("%Y-%m-%d")),
        (ENTRY_ID['posizione'], posizione),
        (ENTRY_ID['sonno'], sonno),
        (ENTRY_ID['energia'], str(energia)),
        (ENTRY_ID['passi'], passi),
        (ENTRY_ID['dolore'], str(dolore)),
        (ENTRY_ID['semaforo'], "5"), # Valore di test
        (ENTRY_ID['note'], f"{feedback} {note_input}")
    ]
    
    # Aggiungi le attività multiple
    for item in attivita:
        payload.append((ENTRY_ID['attivita'], item))
    
    try:
        r = requests.post(URL_MODULO, data=payload)
        if r.status_code == 200:
            st.success("✅ Giornata registrata correttamente!")
        else:
            st.error(f"❌ Errore HTTP {r.status_code}")
    except Exception as e:
        st.error(f"⚠️ Errore: {e}")
