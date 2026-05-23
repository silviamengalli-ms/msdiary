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
    'soimport streamlit as st
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

# --- FUNZIONE METEO AUTOMATICA (FISSATA SU VERONA) ---
def recupera_meteo_automatico(data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        # Coordinate fisse di Verona per evitare errori di geolocalizzazione internet
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        risposta = requests.get(url_meteo).json()
        temp_max = risposta['daily']['temperature_2m_max'][0]
        return float(temp_max) if temp_max is not None else 20.0
    except:
        return 20.0

st.title("📊 Il Mio Diario della Giornata")

@st.cache_data(ttl=5)
def carica_dati(url):
    try: return pd.read_csv(url)
    except: return None

df_storico = carica_dati(URL_FOGLIO_CSV)

# --- INTERFACCIA UTENTE REALE ---
st.subheader("🗓️ Inserisci i dati di oggi")
data_oggi = st.date_input("Data", datetime.date.today())

# Il meteo ora punta sempre a Verona di default
temp_automatica = recupera_meteo_automatico(data_oggi)

st.write("---")
col1, col2 = st.columns(2)

with col1:
    # 📍 Campo posizione messo in cima alla colonna di sinistra, fisso su Verona
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
voto_reale = st.slider("Semaforo energetico", 1.0, 10.0, 5.0, 0.5)

st.write("---")

# --- PULSANTE REGISTRA ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    stringa_attivita = ", ".join(attivita_scelte)
    
    payload = {
        ENTRY_ID['data']: data_oggi.strftime("%Y-%m-%d"),
        ENTRY_ID['temp']: temp_massima,
        ENTRY_ID['sonno']: sonno_scelto,
        ENTRY_ID['energia']: energia,
        ENTRY_ID['passi']: passi_scelti,
        ENTRY_ID['attivita']: stringa_attivita,
        ENTRY_ID['dolore']: int(dolore_livello),
        ENTRY_ID['semaforo']: voto_reale,
        ENTRY_ID['posizione']: posizione_corrente
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

# --- SEZIONE PREDIZIONE AI ---
if st.button("🔮 Calcola Predizione AI"):
    st.info("Funzione AI attiva. Calcolo in corso basato sullo storico attuale...")nno': 'entry.1643446045',
    'energia': 'entry.1042761612',
    'passi': 'entry.111812166',
    'attivita': 'entry.1729676735',
    'dolore': 'entry.533285942',
    'semaforo': 'entry.317549883',
    'posizione': 'entry.507425624'  # ID aggiornato per il campo Posizione!
}

# --- CARICAMENTO DATI PER AI ---
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# --- FUNZIONE METEO AUTOMATICA ---
def recupera_meteo_automatico(lat, lon, data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        risposta = requests.get(url_meteo).json()
        temp_max = risposta['daily']['temperature_2m_max'][0]
        return float(temp_max) if temp_max is not None else 20.0
    except:
        return 20.0

# --- FUNZIONE GEOLOCALIZZAZIONE IP ---
def rileva_posizione_ip():
    try:
        risposta = requests.get("https://ipapi.co/json/").json()
        citta = risposta.get("city", "Verona")
        lat = risposta.get("latitude", 45.43)
        lon = risposta.get("longitude", 10.99)
        return citta, lat, lon
    except:
        return "Verona", 45.43, 10.99

st.title("📊 Il Mio Diario della Giornata")

@st.cache_data(ttl=5)
def carica_dati(url):
    try: return pd.read_csv(url)
    except: return None

df_storico = carica_dati(URL_FOGLIO_CSV)

# --- LOCALIZZAZIONE AUTOMATICA ---
citta_rilevata, lat_rilevata, lon_rilevata = rileva_posizione_ip()

# --- INTERFACCIA UTENTE REALE ---
st.subheader("🗓️ Inserisci i dati di oggi")
data_oggi = st.date_input("Data", datetime.date.today())

# Il meteo calcola la temperatura in base a dove ti trovi
temp_automatica = recupera_meteo_automatico(lat_rilevata, lon_rilevata, data_oggi)

st.write("---")
col1, col2 = st.columns(2)

with col1:
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
# Campo posizione precompilato con la città rilevata automaticamente
posizione_corrente = st.text_input("📍 Ti trovi a:", value=citta_rilevata)

voto_reale = st.slider("Semaforo energetico", 1.0, 10.0, 5.0, 0.5)

st.write("---")

# --- PULSANTE REGISTRA TRAMITE GOOGLE MODULI ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    stringa_attivita = ", ".join(attivita_scelte)
    
    payload = {
        ENTRY_ID['data']: data_oggi.strftime("%Y-%m-%d"),
        ENTRY_ID['temp']: temp_massima,
        ENTRY_ID['sonno']: sonno_scelto,
        ENTRY_ID['energia']: energia,
        ENTRY_ID['passi']: passi_scelti,
        ENTRY_ID['attivita']: stringa_attivita,
        ENTRY_ID['dolore']: int(dolore_livello),
        ENTRY_ID['semaforo']: voto_reale,
        ENTRY_ID['posizione']: posizione_corrente
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

# --- SEZIONE PREDIZIONE AI ---
if st.button("🔮 Calcola Predizione AI"):
    st.info("Funzione AI attiva. Calcolo in corso basato sullo storico attuale...")
