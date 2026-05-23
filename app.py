import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- CONFIGURAZIONE GOOGLE MODULI (ID AGGIORNATI DA SORGENTE) ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'data_comp': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933'
}

# --- CARICAMENTO DATI PER AI ---
URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# --- FUNZIONE METEO AUTOMATICA ---
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

# --- INTERFACCIA UTENTE ---
st.subheader("🗓️ Inserisci i dati di oggi")
data_oggi = st.date_input("Data di riferimento", datetime.date.today())

temp_automatica = recupera_meteo_automatico(data_oggi)

st.write("---")
col1, col2 = st.columns(2)

with col1:
    posizione_corrente = st.text_input("📍 Ti trovi a:", value="Verona")
    temp_massima = st.number_input("Temperatura meteorologica massima (°C)", value=temp_automatica, step=0.5)
    sonno_scelto = st.selectbox("Qualità del sonno", ["soddisfacente", "discreta", "scarsa"])
    energia = st.slider("Energia al risveglio", 1.0, 10.0, 5.0, 1.0)

with col2:
    # Nota: Rimosso il menu passi non presente negli ID del modulo sorgente
    attivita_scelte = st.multiselect(
        "Attività", 
        ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"]
    )
    dolore_livello = st.slider("Livello indolenzimento/dolore", 1.0, 10.0, 1.0, 1.0)

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
                if "Energia" in col or "risveq" in col: media_energia_storica = df_storico[col].mean()
                if "semaforo" in col: media_semaforo_storico = df_storico[col].mean()
                if "indolenzimento" in col or "dolore" in col: media_dolore_storico = df_storico[col].mean()
        except: 
            pass

    differenza_energia = energia - media_energia_storica
    differenza_dolore = dolore_livello - media_dolore_storico
    predizione = media_semaforo_storico + (differenza_energia * 0.6) - (differenza_dolore * 0.4)
    semaforo_reale_calcolato = round(max(1.0, min(10.0, predizione)), 1)
    st.session_state['semaforo_predetto'] = semaforo_reale_calcolato
    
    if semaforo_reale_calcolato >= 6.0: 
        st.success(f"🟢 Semaforo: **{semaforo_reale_calcolato}**")
    elif semaforo_reale_calcolato >= 4.0: 
        st.warning(f"🟡 Semaforo: **{semaforo_reale_calcolato}**")
    else: 
        st.error(f"🔴 Semaforo: **{semaforo_reale_calcolato}**")

valore_semaforo_da_salvare = st.session_state.get('semaforo_predetto', 5.0)

st.write("---")
voto_reale = st.slider("Semaforo energetico finale da registrare", 1.0, 10.0, float(round(valore_semaforo_da_salvare)), 1.0)

st.write("---")

# --- PULSANTE REGISTRA DEFINITIVO ---
if st.button("💾 Registra Giornata nel Database", type="primary"):
    
    # Costruiamo il payload con i nuovi ID corretti
    payload_lista = [
        (ENTRY_ID['data_comp'], data_oggi.strftime("%Y-%m-%d")),
        (ENTRY_ID['posizione'], posizione_corrente),
        (ENTRY_ID['temp'], str(round(temp_massima, 1)).replace('.', ',')),
        (ENTRY_ID['sonno'], sonno_scelto),
        (ENTRY_ID['energia'], str(int(energia))),
        (ENTRY_ID['dolore'], str(int(dolore_livello))),
        (ENTRY_ID['semaforo'], str(int(voto_reale)))
    ]
    
    # Aggiungiamo le opzioni multiple per le attività (Google vuole un elemento per ogni scelta)
    if attivita_scelte:
        for att in attivita_scelte:
            payload_lista.append((ENTRY_ID['attivita'], att))
    else:
        payload_lista.append((ENTRY_ID['attivita'], ""))
        
    try:
        response = requests.post(URL_MODULO, data=payload_lista)
        if response.status_code == 200:
            st.success("🎉 Giornata registrata con successo nel database!")
        else:
            st.error(f"❌ Errore del server Google: {response.status_code}")
    except Exception as e:
        st.error(f"💥 Errore di connessione: {e}")
