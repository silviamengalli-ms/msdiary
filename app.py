import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="MS Diary - Versione Stabile", layout="centered")

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

# --- FUNZIONI ---
def recupera_meteo(data):
    try:
        data_str = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0])
    except: return 20.0

# --- INTERFACCIA ---
st.title("📊 Diario MS (Versione Stabile)")
col1, col2 = st.columns(2)

with col1:
    data_sel = st.date_input("Data:", value=datetime.date.today())
    posizione = st.text_input("Luogo:", value="Verona")
    temp = st.number_input("Temperatura (°C):", value=recupera_meteo(data_sel))
    sonno = st.selectbox("Sonno:", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia (1-10):", 1, 10, 5)

with col2:
    passi = st.selectbox("Passi:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
    # NOTA: qui ho cambiato in radio/selectbox per evitare errori di invio multiplo
    attivita_singola = st.selectbox("Attività (selezione singola):", 
                                   ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])
    dolore = st.slider("Dolore (1-10):", 1, 10, 1)

note_input = st.text_area("Note:")
feedback = st.selectbox("Feedback:", ["#Match", "#Overestimate", "#Underestimate"])

# --- INVIO ---
if st.button("💾 REGISTRA GIORNATA"):
    payload = {
        ENTRY_ID['data']: data_sel.strftime("%Y-%m-%d"),
        ENTRY_ID['posizione']: posizione,
        ENTRY_ID['temp']: str(int(temp)),
        ENTRY_ID['sonno']: sonno,
        ENTRY_ID['energia']: str(energia),
        ENTRY_ID['dolore']: str(dolore),
        ENTRY_ID['semaforo']: "5",
        ENTRY_ID['passi']: passi,
        ENTRY_ID['note']: f"{feedback} {note_input}",
        ENTRY_ID['attivita']: attivita_singola
    }
    
    try:
        r = requests.post(URL_MODULO, data=payload)
        if r.status_code == 200:
            st.success("✅ Dati inviati! Ora puoi andare dalla dottoressa tranquilla.")
        else:
            st.error(f"❌ Errore HTTP {r.status_code}. Riprova.")
    except Exception as e:
        st.error(f"⚠️ Errore di connessione: {e}")
