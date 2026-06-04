import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - MS Diary", layout="centered", page_icon="🔋")

# L'URL DEVE FINIRE CON "formResponse" PER RICEVERE I DATI
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSdtqnrzl71uqLgb1-wY5yw3R2vo7m8-nSwGgNf7ZtbrchqlYw/formResponse"

# MAPPATURA ESATTA ESTRATTA DAL TUO LINK
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

# --- STATO INIZIALE (Memoria dell'app) ---
if 'mattina_salvata' not in st.session_state:
    st.session_state.update({
        'mattina_salvata': False,
        'mattina_data': None, 
        'posizione': 'Verona',
        'temp': 20.0, 
        'umidita': 50, 
        'sonno': 'discreta', 
        'passi': 'da 1001 a 3000', 
        'energia': 5, 
        'attivita': [], 
        'valore_sem': None
    })

# --- FUNZIONI METEO ---
@st.cache_data(ttl=3600)
def recupera_meteo(data):
    try:
        d = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={d}&end_date={d}&daily=temperature_2m_max,relative_humidity_2m_mean&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0]), int(resp['daily']['relative_humidity_2m_mean'][0])
    except: 
        return 20.0, 50

# --- INTERFACCIA ---
st.title("🔋 La Mia Carica")
tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

# ==========================================
# TAB MATTINA
# ==========================================
with tab_mattina:
    data_sel = st.date_input("🗓️ Data:", value=datetime.date.today())
    posizione_input = st.text_input("📍 Posizione:", value=st.session_state.posizione)
    temp_api, umidita_api = recupera_meteo(data_sel)
    
    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("🌡️ Temperatura prevista (°C):", value=temp_api)
        st.info(f"💧 Umidità media prevista: {umidita_api}%")
        sonno = st.selectbox("💤 Qualità del sonno:", ["discreta", "soddisfacente", "scarsa"])
    with col2:
        passi = st.selectbox("🚶 Passi previsti:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
        energia = st.slider("⚡ Energia al risveglio (1-10):", 1, 10, 5)
    
    attivita = st.multiselect("📅 Attività in programma:", 
                              ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        # Logica Pesi
        pesi = {
            "ufficio": -0.5, "lavoro da casa": -0.2, "piccole commissioni": -0.4, 
            "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "sociale": -0.7
        }
        
        somma_att = sum([pesi[a] for a in attivita])
        if len(attivita) > 1:
            somma_att += (len(attivita) - 1) * -0.3
            
        p_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3)
        
        peso_sonno = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}[sonno]
        peso_passi = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.3}[passi]
        
        score = 5.0 + (energia * 0.3) + peso_sonno + peso_passi + somma_att + p_temp
        valore_calcolato = round(max(1.0, min(10.0, score)), 1)
        
        # Salvataggio in sessione
        st.session_state.update({
            'mattina_salvata': True,
            'mattina_data': data_sel, 
            'posizione': posizione_input,
            'temp': temp, 
            'umidita': umidita_api, 
            'sonno': sonno, 
            'passi': passi, 
            'energia': energia, 
            'attivita': attivita, 
            'valore_sem': valore_calcolato
        })
        
        st.success("✅ Dati della mattina salvati in memoria! Ora puoi passare alla scheda serale a fine giornata.")
        
        # Visualizzazione Semforo
        if valore_calcolato <= 4.5:
            st.error(f"🔴 BOLLINO ROSSO: {valore_calcolato}")
        elif valore_calcolato <= 7.0:
            st.warning(f"🟡 BOLLINO GIALLO: {valore_calcolato}")
        else:
            st.success(f"🟢 BOLLINO VERDE: {valore_calcolato}")


# ==========================================
# TAB SERA
# ==========================================
with tab_sera:
    if not st.session_state.mattina_salvata:
        st.warning("⚠️ Compila e salva prima i dati della mattina!")
    else:
        st.markdown(f"### 🚦 Semaforo stimato stamattina: **{st.session_state.valore_sem}**")
        
        valutazione = st.selectbox("Riscontro rispetto alla previsione:", ["Match", "Overestimated", "Underestimated"])
        dolore = st.slider("Livello dolore avvertito (1-10):", 1, 10, 1)
        note = st.text_area("Note e riflessioni serali:", placeholder="#sintomi #clima #umore")
        
        if st.button("💾 REGISTRA GIORNATA DEFINITIVA", use_container_width=True):
            
            # Formattiamo le attività come stringa unica
            stringa_attivita = ", ".join(st.session_state.attivita) if st.session_state.attivita else "Nessuna"
            
            # Costruzione esatta del payload con i dati convertiti in stringhe
            payload = {
                ENTRY_ID['data']: st.session_state.mattina_data.strftime("%d/%m/%Y"),
                ENTRY_ID['posizione']: st.session_state.posizione,
                ENTRY_ID['temp']: str(int(st.session_state.temp)),
                ENTRY_ID['umidita']: str(st.session_state.umidita),
                ENTRY_ID['sonno']: st.session_state.sonno,
                ENTRY_ID['energia']: str(st.session_state.energia),
                ENTRY_ID['attivita']: stringa_attivita,
                ENTRY_ID['passi']: st.session_state.passi,
                ENTRY_ID['semaforo']: str(int(round(st.session_state.valore_sem))),
                ENTRY_ID['valutazione']: valutazione,
                ENTRY_ID['dolore']: str(dolore),
                ENTRY_ID['note']: note
            }
            
            try:
                r = requests.post(URL_MODULO, data=payload)
                if r.status_code == 200:
                    st.balloons()
                    st.success("✅ Dati inviati con successo al tuo Google Sheet! Ottimo lavoro oggi. 🌟")
                    # Opzionale: resetta la memoria dopo l'invio
                    # st.session_state.mattina_salvata = False 
                else:
                    st.error(f"❌ Errore dal server (Codice {r.status_code}). I dati non sono stati salvati.")
            except Exception as e:
                st.error(f"⚠️ Errore di connessione a Google Forms: {e}")
