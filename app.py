import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"
ENTRY_ID = {
    'posizione': 'entry.1412086707', 'temp': 'entry.1900939990', 'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247', 'attivita': 'entry.1595201387', 'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933', 'passi': 'entry.1805134602'
}
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# --- FUNZIONI ---
def recupera_meteo_automatico(data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        return float(requests.get(url_meteo).json()['daily']['temperature_2m_max'][0])
    except: return 20.0

st.title("📊 Il Mio Diario & Predittore")
df_storico = pd.read_csv(URL_FOGLIO_CSV) if True else None

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    posizione = st.text_input("📍 Luogo:", value="Verona")
    temp = st.number_input("Temperatura (°C)", value=recupera_meteo_automatico(datetime.date.today()))
    sonno = st.selectbox("Sonno", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia (1-10)", 1, 10, 5)
with col2:
    passi = st.selectbox("Passi", ["fino a 1000", "da 1001 a 3000", "oltre 3000"])
    attivita = st.multiselect("Attività", ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])
    dolore = st.slider("Dolore (1-10)", 1, 10, 1)

# --- PREDIZIONE AI ---
st.subheader("🔮 Calcolo del Semaforo")
if st.button("🔄 Calcola Predizione AI"):
    media_en = df_storico['Energia'].mean() if 'Energia' in df_storico.columns else 5.0
    media_dol = df_storico['Dolore'].mean() if 'Dolore' in df_storico.columns else 1.0
    
    predizione = 5.0 + ((energia - media_en) * 0.6) - ((dolore - media_dol) * 0.4)
    semaforo_pred = round(max(1.0, min(10.0, predizione)), 1)
    
    st.session_state['semaforo_predetto'] = semaforo_pred
    st.write(f"### Il tuo Semaforo predetto: **{semaforo_pred}**")

valore_da_registrare = st.slider("Semaforo finale da salvare", 1, 10, int(st.session_state.get('semaforo_predetto', 5.0)))

# --- REGISTRAZIONE ---
if st.button("💾 Registra Giornata", type="primary"):
    payload = {
        ENTRY_ID['posizione']: posizione, 
        ENTRY_ID['temp']: str(int(temp)), 
        ENTRY_ID['sonno']: sonno,
        ENTRY_ID['energia']: str(energia), 
        ENTRY_ID['dolore']: str(dolore), 
        ENTRY_ID['semaforo']: str(valore_da_registrare), 
        ENTRY_ID['passi']: passi
    }
    
    payload_list = list(payload.items()) + [(ENTRY_ID['attivita'], a) for a in attivita]
    
    if requests.post(URL_MODULO, data=payload_list).status_code == 200:
        st.success("🎉 Salvato!")
    else:
        st.error("Errore di registrazione.")
