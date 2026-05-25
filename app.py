import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="MS Diary - Completo", layout="centered")

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

PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.5}
PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.1, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.4, "riposo totale": 0.5, "sociale": -0.7
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
st.title("📊 Diario MS Completo")

col1, col2 = st.columns(2)
with col1:
    data_sel = st.date_input("Data:", value=datetime.date.today())
    posizione = st.text_input("Luogo:", value="Verona")
    temp = st.number_input("Temperatura (°C):", value=recupera_meteo(data_sel))
    sonno = st.selectbox("Sonno:", list(PESI_SONNO.keys()))
    energia = st.slider("Energia (1-10):", 1, 10, 5)

with col2:
    passi = st.selectbox("Passi:", list(PESI_PASSI.keys()))
    attivita = st.multiselect("Attività:", list(PESI_ATTIVITA.keys()))
    dolore = st.slider("Dolore (1-10):", 1, 10, 1)

# --- CALCOLO SEMAFORO ---
score = 3.0 + (energia * 0.4) + PESI_SONNO[sonno] + PESI_PASSI[passi] + sum([PESI_ATTIVITA[a] for a in attivita])
valore_sem = round(max(1.0, min(10.0, score)), 1)
st.metric("🔮 Semaforo Energetico", valore_sem)

note_input = st.text_area("Note:")

# --- INVIO ---
if st.button("💾 REGISTRA GIORNATA"):
    # Costruiamo la lista di tuple per permettere i duplicati (checkbox)
    dati_invio = [
        (ENTRY_ID['data'], data_sel.strftime("%Y-%m-%d")),
        (ENTRY_ID['posizione'], posizione),
        (ENTRY_ID['temp'], str(int(temp))),
        (ENTRY_ID['sonno'], sonno),
        (ENTRY_ID['energia'], str(energia)),
        (ENTRY_ID['passi'], passi),
        (ENTRY_ID['dolore'], str(dolore)),
        (ENTRY_ID['semaforo'], str(int(valore_sem))),
        (ENTRY_ID['note'], note_input)
    ]
    
    # Aggiungi ogni attività singolarmente come voce ripetuta
    for a in attivita:
        dati_invio.append((ENTRY_ID['attivita'], a))
        
    try:
        r = requests.post(URL_MODULO, data=dati_invio)
        if r.status_code == 200:
            st.success("✅ Dati registrati con successo!")
        else:
            st.error(f"❌ Errore HTTP {r.status_code}. Il server ha rifiutato la richiesta.")
    except Exception as e:
        st.error(f"⚠️ Errore di connessione: {e}")
