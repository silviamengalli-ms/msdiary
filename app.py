import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE GOOGLE MODULI (AGGIORNATA AL NUOVO FORM) ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSclLdf0eA6rO_gJAtCAsgDco_wU60b0q-O2Zcl5D88Zk-fAnQ/formResponse"

ENTRY_ID = {
    'temp': 'entry.232332158',
    'sonno': 'entry.1764614275',
    'energia': 'entry.1165485458',
    'passi': 'entry.571477759',
    'attivita': 'entry.1492025171',
    'dolore': 'entry.460775323',
    'semaforo': 'entry.44490089',
    'posizione': 'entry.492160682'
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
        return pd.read_csv(url)
    except: 
        return None

df_storico = carica_dati(URL_FOGLIO_CSV)

# --- INTERFACCIA UTENTE REALE ---
st.subheader("🗓️ Inserisci i dati di oggi")
data_oggi = st.date_input("Data di riferimento per il meteo", datetime.date.today())

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

# --- SEZIONE PREDIZIONE AI ---
st.subheader("🔮 Calcolo del Semaforo Energetico")

if st.button("🔄 Calcola Predizione AI", type="secondary"):
    media_energia_storica = 5.0
    media_semaforo_storico = 5.0
    media_dolore_storico = 1.0

    if df_storico is not None and not df_storico.empty:
        try:
            for col in df_storico.columns:
                if "Energia" in col or "risveq" in col:
                    media_energia_storica = df_storico[col].mean()
                if "semaforo" in col:
                    media_semaforo_storico = df_storico[col].mean()
                if "indolenzimento" in col or "dolore" in col:
                    media_dolore_storico = df_storico[col].mean()
        except:
            pass

    differenza_energia = energia - media_energia_storica
    differenza_dolore = dolore_livello - media_dolore_storico
    predizione = media_semaforo_storico + (differenza_energia * 0.6) - (differenza_dolore * 0.4)
    semaforo_reale_calcolato = round(max(1.0, min(10.0, predizione)), 1)
    
    st.session_state['semaforo_predetto'] = semaforo_reale_calcolato
    
    if semaforo_reale_calcolato >= 6.0:
        st.success(f"🟢 Semaforo Energetico Rilevato: **{semaforo_reale_calcolato}** (Giornata Buona/Carica)")
    elif semaforo_reale_calcolato >= 4.0:
        st.warning(f"🟡 Semaforo Energetico Rilevato: **{semaforo_reale_calcolato}** (Giornata Media/Attenzione)")
    else:
        st.error(f"🔴 Semaforo Energetico Rilevato: **{semaforo_reale_calcolato}** (Giornata Scarica/Riposo)")

valore_semaforo_da_salvare = st.session_state.get('semaforo_predetto', 5.0)

st.write("---")
voto_reale = st.slider("Semaforo energetico finale da registrare", 1.0, 10.0, float(valore_semaforo_da_salvare), 0.5)

st.write("---")

# --- PULSANTE REGISTRA ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    stringa_attivita = ", ".join(attivita_scelte)
    
    payload = {
        ENTRY_ID['temp']: str(temp_massima).replace('.', ','),
        ENTRY_ID['sonno']: str(sonno_scelto),
        ENTRY_ID['energia']: str(energia).replace('.', ','),
        ENTRY_ID['passi']: str(passi_scelti),
        ENTRY_ID['attivita']: str(stringa_attivita),
        ENTRY_ID['dolore']: str(int(dolore_livello)),
        ENTRY_ID['semaforo']: str(voto_reale).replace('.', ','),
        ENTRY_ID['posizione']: str(posizione_corrente)
    }
    
    try:
        response = requests.post(URL_MODULO, data=payload)
        if response.status_code == 200:
            st.balloons()
            st.success("✅ Dati inviati al Modulo e registrati sul Foglio Google!")
        else:
            st.error("❌ Errore nell'invio. Verifica la connessione dell'app.")
    except:
        st.error("❌ Errore di connessione con il server di Google.")
