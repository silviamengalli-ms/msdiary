import streamlit as st
import pandas as pd
import datetime
import requests

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="MS Diary - Predizione", layout="centered")

# --- COSTANTI & ID ---
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

# --- PARAMETRI LOGICA AI ---
PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.5}
PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.1, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.4, "riposo totale": 0.5, "sociale": -0.7
}

# --- FUNZIONE METEO ---
def recupera_meteo(data):
    try:
        data_str = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0])
    except: return 20.0

# --- INTERFACCIA UTENTE ---
st.title("📊 Il Mio Diario & Predittore")

col1, col2 = st.columns(2)
with col1:
    data_sel = st.date_input("Data:", value=datetime.date.today(), format="DD/MM/YYYY")
    posizione = st.text_input("Luogo:", value="Verona")
    temp = st.number_input("Temperatura (°C):", value=recupera_meteo(data_sel))
    sonno = st.selectbox("Sonno:", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia (1-10):", 1, 10, 5)

with col2:
    passi = st.selectbox("Passi:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
    attivita = st.multiselect("Attività:", list(PESI_ATTIVITA.keys()))
    dolore = st.slider("Dolore (1-10):", 1, 10, 1)

# --- CALCOLO SEMAFORO ---
st.subheader("🔮 Semaforo")
if st.button("🔄 Calcola Predizione AI"):
    score = 3.0 + (energia * 0.4) + PESI_SONNO.get(sonno, 0) + PESI_PASSI.get(passi, 0) + sum([PESI_ATTIVITA.get(a, 0) for a in attivita])
    st.session_state['sem'] = round(max(1.0, min(10.0, score)), 1)

valore_sem = st.session_state.get('sem', 5.0)
st.write(f"Valore calcolato: {valore_sem}")

# --- NOTE E INVIO ---
note_input = st.text_area("Note (usa tag):")
feedback = st.selectbox("Feedback:", ["#Match", "#Overestimate", "#Underestimate"])

if st.button("💾 Registra Giornata"):
    # Prepariamo la lista dei dati da inviare
    dati = [
        (ENTRY_ID['data'], data_sel.strftime("%Y-%m-%d")),
        (ENTRY_ID['posizione'], posizione),
        (ENTRY_ID['temp'], str(int(temp))),
        (ENTRY_ID['sonno'], sonno),
        (ENTRY_ID['energia'], str(energia)),
        (ENTRY_ID['dolore'], str(dolore)),
        (ENTRY_ID['semaforo'], str(int(round(valore_sem)))),
        (ENTRY_ID['passi'], passi),
        (ENTRY_ID['note'], f"{feedback} {note_input}")
    ]
    
    # Aggiunta attività multiple (chiave ripetuta per checkbox)
    for a in attivita:
        dati.append((ENTRY_ID['attivita'], a))
        
    try:
        r = requests.post(URL_MODULO, data=dati)
        if r.status_code == 200:
            st.success("✅ Giornata registrata correttamente!")
        else:
            st.error(f"❌ Errore HTTP {r.status_code}: Il modulo non ha accettato i dati.")
    except Exception as e:
        st.error(f"⚠️ Errore di connessione: {e}")
