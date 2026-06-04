import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - MS Diary", layout="centered", page_icon="🔋")

# URL DEFINITIVO (Punta al formResponse del modulo ufficiale)
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

# MAPPATURA COMPLETA E CORRETTA AL 100% DEL TUO MODULO DEFINITIVO
ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'umidita': 'entry.2086318809',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'passi': 'entry.28384771',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'valutazione': 'entry.2023032977',
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

# --- FUNZIONI METEO CON GEOLOCALIZZAZIONE DINAMICA ---
@st.cache_data(ttl=3600)
def recupera_meteo(data, nome_citta):
    try:
        url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={nome_citta}&count=1&language=it&format=json"
        risposta_geo = requests.get(url_geo).json()
        
        lat, lon = 45.43, 10.99 
        if "results" in risposta_geo and len(risposta_geo["results"]) > 0:
            lat = risposta_geo["results"][0]["latitude"]
            lon = risposta_geo["results"][0]["longitude"]
            
        d = data.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={d}&end_date={d}&daily=temperature_2m_max,relative_humidity_2m_mean&timezone=Europe/Rome"
        resp = requests.get(url_meteo).json()
        return float(resp['daily']['temperature_2m_max'][0]), int(resp['daily']['relative_humidity_2m_mean'][0])
    except: 
        return 20.0, 50

# --- INTERFACCIA ACCOGLIENTE ---
st.title("🔋 La Mia Carica")
st.markdown("---")
st.markdown("Buongiorno! Prepariamoci per affrontare la giornata 😊")

tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

# ==========================================
# TAB MATTINA (Pianificazione)
# ==========================================
with tab_mattina:
    # 1. CREIAMO LE DUE COLONNE PER LA PRIMA RIGA (Data/Luogo vs Meteo)
    col1, col2 = st.columns(2)
    
    with col1:
        data_sel = st.date_input("🗓️ Data:", value=datetime.date.today())
        posizione_input = st.text_input("📍 Posizione:", value=st.session_state.posizione)
    
    # TRUCCO DI COERENZA: Recuperiamo il meteo subito dopo gli input di col1, così col2 ha i dati pronti!
    temp_api, umidita_api = recupera_meteo(data_sel, posizione_input)
    
    with col2:
        temp = st.number_input("🌡️ Temperatura prevista (°C):", value=temp_api)
        # Sistemata la sintassi dell'input numerico dell'umidità
        umidita = st.number_input("💧 Umidità media prevista (%):", value=int(umidita_api))
    
    st.markdown("---") # Linea di separazione elegante
    
    # 2. DA QUI IN POI IL CODICE È FUORI DALLE COLONNE, QUINDI APPARIRÀ A COLONNA UNICA (TUTTA LARGHEZZA)
    sonno = st.selectbox("💤 Qualità del sonno:", ["discreta", "soddisfacente", "scarsa"])
    passi = st.selectbox("🚶 Passi previsti:", ["fino a 1000", "da 1001 a 3000", "oltre i 3000"])
    energia = st.slider("⚡ Energia al risveglio (1-10):", 1, 10, 5)
    
    attivita = st.multiselect("📅 Attività in programma:", 
                              ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        # Logica Pesi Definitiva
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
        
        # Congelamento dei dati mattutini nella sessione
        st.session_state.update({
            'mattina_salvata': True,
            'mattina_data': data_sel, 
            'posizione': posizione_input,
            'temp': temp, 
            'umidita': umidita, # Usiamo il valore modificabile inserito nel widget
            'sonno': sonno, 
            'passi': passi, 
            'energia': energia, 
            'attivita': attivita, 
            'valore_sem': valore_calcolato
        })
        

        st.markdown("---") 
        
        if valore_calcolato <= 4.5:
            st.error(f"🔴 BOLLINO ROSSO: {valore_calcolato} La tua energia stimata è bassa oggi. Cerca di dare priorità al riposo e non sovraccaricarti 🐢")
        elif valore_calcolato <= 7.0:
            st.warning(f"🟡 BOLLINO GIALLO: {valore_calcolato} Giornata regolare. Procedi con calma e occhio a non esagerare 🐘")
        else:
            st.success(f"🟢 BOLLINO VERDE: {valore_calcolato} Ottimo! Hai una buona carica per affrontare la giornata con serenità 🦋")


        st.write("✅ Dati della mattina salvati in memoria! Vediamoci stasera per registrare il feedback")
# ==========================================
# TAB SERA (Consuntivo e Invio)
# ==========================================
with tab_sera:
    if not st.session_state.mattina_salvata:
        st.warning("⚠️ Compila e salva prima i dati del mattino nella scheda precedente!")
    else:
        st.subheader("Com'è andata la giornata?")
        st.markdown(f"Stamattina il sistema aveva previsto un semaforo di: **{st.session_state.valore_sem}**")
        
        valutazione = st.selectbox("Il punteggio del mattino era corretto? (Riscontro):", ["Match", "Overestimated", "Underestimated"])
        dolore = st.slider("Livello dolore avvertito (1-10):", 1, 10, 1)
        note = st.text_area("Note o riflessioni serali:", placeholder="Scrivi qui le tue annotazioni... (#sintomi, #clima, #umore)")
        
        if st.button("💾 REGISTRA IL MIO DIARIO", use_container_width=True):
            
            stringa_attivita_completa = ", ".join(st.session_state.attivita) if st.session_state.attivita else "Nessuna"
            note_finali = f"[Attività svolte: {stringa_attivita_completa}] {note}".strip()
            
            payload = {
                ENTRY_ID['data']: st.session_state.mattina_data.strftime("%d/%m/%Y"),
                ENTRY_ID['posizione']: st.session_state.posizione,
                ENTRY_ID['temp']: str(int(round(st.session_state.temp))),
                ENTRY_ID['umidita']: str(int(st.session_state.umidita)),
                ENTRY_ID['sonno']: st.session_state.sonno,
                ENTRY_ID['energia']: str(int(st.session_state.energia)),
                ENTRY_ID['passi']: st.session_state.passi,
                ENTRY_ID['semaforo']: str(int(round(st.session_state.valore_sem))),
                ENTRY_ID['valutazione']: valutazione,
                ENTRY_ID['dolore']: str(int(dolore)),
                ENTRY_ID['note']: note_finali
            }
            
            if st.session_state.attivita:
                payload[ENTRY_ID['attivita']] = st.session_state.attivita[0]
            else:
                payload[ENTRY_ID['attivita']] = "riposo totale"
            
            try:
                r = requests.post(URL_MODULO, data=payload)
                if r.status_code == 200:
                    st.balloons()
                    st.write("✅ Dati registrati con successo nel tuo diario! Buona notte e sogni d'oro! 🌟")
                    st.session_state.mattina_salvata = False 
                else:
                    st.error(f"❌ Errore di salvataggio (Codice HTTP {r.status_code}). Verifica la configurazione dei campi.")
            except Exception as e:
                st.error(f"⚠️ Impossibile raggiungere Google Moduli: {e}")
