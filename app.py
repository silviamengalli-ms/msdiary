import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - MS Diary", layout="centered", page_icon="🔋")

URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'umidita': 'entry.1051612516',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'passi': 'entry.28384771',
    'semaforo': 'entry.625659299',
    'valutazione': 'entry.375319797',
    'dolore': 'entry.672372933',
    'note': 'entry.158362423'
}

# --- STATO INIZIALE ---
if 'mattina_data' not in st.session_state:
    st.session_state.update({
        'mattina_data': None, 'temp': 20.0, 'umidita': 50, 'sonno': 'discreta', 
        'passi': 'da 1001 a 3000', 'energia': 5, 'attivita': [], 'valore_sem': None
    })

# --- FUNZIONI METEO ---
@st.cache_data(ttl=3600)
def recupera_meteo(data):
    try:
        d = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={d}&end_date={d}&daily=temperature_2m_max,relative_humidity_2m_mean&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0]), int(resp['daily']['relative_humidity_2m_mean'][0])
    except: return 20.0, 50

# --- INTERFACCIA ---
st.title("🔋 La Mia Carica")
tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

with tab_mattina:
    data_sel = st.date_input("🗓️ Data:", value=datetime.date.today())
    temp_api, umidita_api = recupera_meteo(data_sel)
    
    col1, col2 = st.columns(2)
    with col1:
        temp = st.slider("🌡️ Temperatura (°C):", -5.0, 45.0, temp_api, 0.5)
        st.info(f"💧 Umidità media prevista: {umidita_api}%")
        sonno = st.selectbox("💤 Qualità sonno:", ["discreta", "soddisfacente", "scarsa"])
    with col2:
        passi = st.selectbox("🚶 Passi:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
        energia = st.slider("⚡ Energia:", 1, 10, 5)
    
    attivita = st.multiselect("📅 Attività:", ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina"):
        # Logica Pesi
        pesi = {"ufficio": -0.5, "lavoro da casa": -0.2, "piccole commissioni": -0.4, "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "sociale": -0.7}
        somma_att = sum([pesi[a] for a in attivita]) + ((len(attivita)-1)*-0.3 if len(attivita)>1 else 0)
        p_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3)
        
        score = 5.0 + (energia * 0.3) + {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}[sonno] + {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.3}[passi] + somma_att + p_temp
        
        st.session_state.update({'mattina_data': data_sel, 'temp': temp, 'umidita': umidita_api, 'sonno': sonno, 'passi': passi, 'energia': energia, 'attivita': attivita, 'valore_sem': round(max(1.0, min(10.0, score)), 1)})
        st.success(f"Mattina salvata! Semaforo stimato: {st.session_state.valore_sem}")

with tab_sera:
    if st.session_state.valore_sem is None:
        st.warning("⚠️ Pianifica prima la mattina!")
    else:
        st.write(f"### Semaforo di oggi: {st.session_state.valore_sem}")
        dolore = st.slider("Livello dolore (1-10):", 1, 10, 1)
        note = st.text_area("Note serali:")
        
        if st.button("💾 Invia Report Finale"):
            payload = {
                ENTRY_ID['data']: st.session_state.mattina_data.strftime("%d/%m/%Y"),
                ENTRY_ID['temp']: str(st.session_state.temp),
                ENTRY_ID['umidita']: str(st.session_state.umidita),
                ENTRY_ID['sonno']: st.session_state.sonno,
                ENTRY_ID['energia']: str(st.session_state.energia),
                ENTRY_ID['passi']: st.session_state.passi,
                ENTRY_ID['attivita']: ", ".join(st.session_state.attivita),
                ENTRY_ID['semaforo']: str(st.session_state.valore_sem),
                ENTRY_ID['dolore']: str(dolore),
                ENTRY_ID['note']: note
            }
            requests.post(URL_MODULO, data=payload)
            st.balloons()
            st.success("Tutto inviato! Riposati ora. 🌟")
