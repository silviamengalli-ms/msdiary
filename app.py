import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE GOOGLE MODULI ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'data': 'entry.811568478',
    'temp': 'entry.170668988',
    'sonno': 'entry.1643446045',
    'energia': 'entry.1042761612',
    'passi': 'entry.111812166',
    'attivita': 'entry.1729676735',
    'dolore': 'entry.533285942',
    'semaforo': 'entry.317549883',
    'posizione': 'entry.507425624'
}

# --- CARICAMENTO DATI PER AI ---
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# --- FUNZIONE METEO AUTOMATICA (VERONA) ---
def recupera_meteo_automatico(data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        risposta = requests.get(url_meteo).json()
        temp_max = risposta['daily']['temperature_2m_max'][0]
        return float(temp_max) if temp_max is not None else 20.0
    except:
        return 20.0

st.title("📊 Il Mio Diario della Giornata")

@st.cache_data(ttl=5)
def carica_dati(url):
    try: 
        # Leggiamo il foglio ignorando eventuali righe vuote
        return pd.read_csv(url).dropna(subset=["Data", "semaforo energetico"])
    except: 
        return None

df_storico = carica_dati(URL_FOGLIO_CSV)

# --- INTERFACCIA UTENTE REALE ---
st.subheader("🗓️ Inserisci i dati di oggi")
data_oggi = st.date_input("Data", datetime.date.today())

temp_automatica = recupera_meteo_automatico(data_oggi)

st.write("---")
col1, col2 = st.columns(2)

with col1:
    posizione_corrente = st.text_input("📍 Ti trovi a:", value="Verona")
    temp_massima = st.number_input("Temperatura meteorologica massima (°C)", value=temp_automatica, step=0.5)
    sonno_scelto = st.selectbox("Qualità del sonno", ["soddisfacente", "discreta", "scarsa"])
    energia = st.slider("Energia al risveglio", 1.0, 10.0, 5.0, 0.5)

with col2:
    passi_scelti = st.selectbox("Passi", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
    attivita_scelte = st.multiselect(
        "Attività", 
        ["sociale", "piccole commissioni", "lavoro da casa", "fisioterapia", "ufficio", "visita", "riposo totale"]
    )
    dolore_livello = st.slider("Livello indolenzimento/dolore", 1.0, 10.0, 1.0, 0.5)

st.write("---")

# --- SEZIONE PREDIZIONE AI (IL SEMAFORO CALCOLATO) ---
st.subheader("🔮 Calcolo del Semaforo Energetico")

if st.button("🔄 Calcola Predizione AI", type="secondary"):
    if df_storico is not None and not df_storico.empty:
        try:
            # 🧠 ALGORITMO DI PREDIZIONE BASATO SUL TUO STORICO REALISTICO
            # Calcoliamo l'impatto medio dei tuoi fattori storici sul semaforo energetico
            media_energia_storica = df_storico["Energia al risvegl"].mean() if "Energia al risvegl" in df_storico.columns else 5.0
            media_semaforo_storico = df_storico["semaforo energetico"].mean()
            
            # Calcoliamo una deviazione basata sull'energia di oggi rispetto alla tua media
            differenza_energia = energia - media_energia_storica
            
            # Correzione basata sul dolore di oggi (più dolore abbassa il semaforo)
            media_dolore_storico = df_storico["livello indolenzimento/dolore"].mean() if "livello indolenzimento/dolore" in df_storico.columns else 1.0
            differenza_dolore = dolore_livello - media_dolore_storico
            
            # Calcolo finale pesato
            predizione = media_semaforo_storico + (differenza_energia * 0.6) - (differenza_dolore * 0.4)
            semaforo_reale_calcolato = round(max(1.0, min(10.0, predizione)), 1)
            
            # Salviamo il valore temporaneamente nella memoria dell'app
            st.session_state['semaforo_predetto'] = semaforo_reale_calcolato
            
            # Mostriamo il risultato con un colore dinamico
            if semaforo_reale_calcolato >= 6.0:
                st.success(f"🟢 Semaforo Energetico Rilevato: **{semaforo_reale_calcolato}** (Giornata Buona/Carica)")
            elif semaforo_reale_calcolato >= 4.0:
                st.warning(f"🟡 Semaforo Energetico Rilevato: **{semaforo_reale_calcolato}** (Giornata Media/Attenzione)")
            else:
                st.error(f"🔴 Semaforo Energetico Rilevato: **{semaforo_reale_calcolato}
