import streamlit as st
import pandas as pd
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
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

URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# --- PARAMETRI DI CALIBRAZIONE ---
PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre 3000": -0.5}
PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.1, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.4, "riposo totale": 0.5, "sociale": -0.7
}

# --- FUNZIONI ---
def recupera_meteo_automatico(data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        response = requests.get(url_meteo)
        return float(response.json()['daily']['temperature_2m_max'][0])
    except:
        return 20.0

# --- INTERFACCIA ---
st.title("📊 Il Mio Diario & Predittore")

try:
    df_storico = pd.read_csv(URL_FOGLIO_CSV)
except:
    df_storico = pd.DataFrame(columns=['Energia', 'Dolore'])

col1, col2 = st.columns(2)
with col1:
    posizione = st.text_input("📍 Luogo:", value="Verona")
    temp = st.number_input("Temperatura (°C)", value=recupera_meteo_automatico(datetime.date.today()))
    sonno = st.selectbox("Sonno", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia al risveglio (1-10):", 1, 10, 5)
with col2:
    passi = st.selectbox("Passi", ["fino a 1000", "da 1001 a 3000", "oltre 3000"])
    attivita = st.multiselect("Attività", ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])
    dolore = st.slider("Dolore (1-10 - dato background):", 1, 10, 1)

note = st.text_area("📝 Note (opzionale):")

# --- LOGICA AI ---
st.subheader("🔮 Stato del Semaforo")

if st.button("🔄 Calcola Predizione AI"):
    # 1. Base di partenza dinamica
    score = 3.0 + (energia * 0.4)
    
    # 2. Somma pesi
    score += PESI_SONNO.get(sonno, 0)
    score += PESI_PASSI.get(passi, 0)
    score += sum([PESI_ATTIVITA.get(a, 0) for a in attivita])
    
    # 3. Logica Termica
    if "riposo totale" not in attivita:
        if temp > 30:
            score -= 2.0 
        elif 20 < temp <= 30:
            score -= 0.8 
    elif "riposo totale" in attivita and temp > 30:
        score -= 0.3 
        
    st.session_state['semaforo_predetto'] = round(max(1.0, min(10.0, score)), 1)

valore = st.session_state.get('semaforo_predetto', 5.0)

if valore <= 5:
    st.error(f"Stato attuale: ROSSO (Valore: {valore})")
elif 6 <= valore <= 8:
    st.warning(f"Stato attuale: GIALLO (Valore: {valore})")
else:
    st.success(f"Stato attuale: VERDE (Valore: {valore})")

valore_da_registrare = st.slider("Conferma o modifica valore finale:", 1, 10, int(valore))

# --- INVIO DATI ---
if st.button("💾 Registra Giornata", type="primary"):
    payload = {
        ENTRY_ID['posizione']: posizione,
        ENTRY_ID['temp']: str(int(temp)),
        ENTRY_ID['sonno']: sonno,
        ENTRY_ID['energia']: str(energia),
        ENTRY_ID['dolore']: str(dolore), 
        ENTRY_ID['semaforo']: str(valore_da_registrare),
        ENTRY_ID['passi']: passi,
        ENTRY_ID['note']: note
    }
    payload_lista = list(payload.items())
    for a in attivita:
        payload_lista.append((ENTRY_ID['attivita'], a))
    
    try:
        response = requests.post(URL_MODULO, data=payload_lista)
        if response.status_code == 200:
            st.success("🎉 Registrazione riuscita!")
        else:
            st.error(f"Errore di invio: {response.status_code}")
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
