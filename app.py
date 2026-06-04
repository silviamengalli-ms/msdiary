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
        # 1. GEOCALIZZAZIONE: Cerchiamo le coordinate del nome inserito dall'utente
        url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={nome_citta}&count=1&language=it&format=json"
        risposta_geo = requests.get(url_geo).json()
        
        # Coordinate di default (Verona) nel caso in cui la ricerca fallisca
        lat, lon = 45.43, 10.99 
        
        if "results" in risposta_geo and len(risposta_geo["results"]) > 0:
            lat = risposta_geo["results"][0]["latitude"]
            lon = risposta_geo["results"][0]["longitude"]
            
        # 2. METEO: Scarichiamo i dati meteo usando le coordinate trovate
        d = data.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={d}&end_date={d}&daily=temperature_2m_max,relative_humidity_2m_mean&timezone=Europe/Rome"
        resp = requests.get(url_meteo).json()
        return float(resp['daily']['temperature_2m_max'][0]), int(resp['daily']['relative_humidity_2m_mean'][0])
    except: 
        # Fallback sicuro in caso di totale assenza di connessione o errore API
        return 20.0, 50

# --- INTERFACCIA ACCOGLIENTE ---
st.title("🔋 La Mia Carica")
st.markdown("---")
st.markdown("Ben svegliata! Prepariamoci per affrontare la giornata 😊")

tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Giornata", "🌌 Feedback Serale"])

# ==========================================
# TAB MATTINA (Pianificazione)
# ==========================================
with tab_mattina:
    data_sel = st.date_input("🗓️ Data:", value=datetime.date.today())
    posizione_input = st.text_input("📍 Posizione:", value=st.session_state.posizione)
    
    # AGGIORNAMENTO: Passiamo il testo della posizione alla funzione meteo
    temp_api, umidita_api = recupera_meteo(data_sel, posizione_input)
    
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

    if st.button("🚀 Calcola e Salva la Previsione per Oggi", use_container_width=True):
        # Logica Pesi Definitiva
        pesi = {
            "ufficio": -0.5, "lavoro da casa": -0.2, "piccole commissioni": -0.4, 
            "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "sociale": -0.7
        }
        
        somma_att = sum([pesi[a] for a in attivita])
        if len(attivita) > 1:
            somma_att += (len(attivita) - 1) * -0.3 # Effetto penalità cumulativa
            
        p_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3) # Penalità caldo
        
        peso_sonno = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}[sonno]
        peso_passi = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.3}[passi]
        
        score = 5.0 + (energia * 0.3) + peso_sonno + peso_passi + somma_att + p_temp
        valore_calcolato = round(max(1.0, min(10.0, score)), 1)
        
        # Congelamento dei dati mattutini nella sessione
        st.session_state.update({
            'mattina_salvata': True,
            'mattina_data': data_sel, 
            'posizione': posizione_input, # Salva la città corretta inserita
            'temp': temp, 
            'umidita': umidita_api, 
            'sonno': sonno, 
            'passi': passi, 
            'energia': energia, 
            'attivita': attivita, 
            'valore_sem': valore_calcolato
        })
        
        st.success("✅ Dati della mattina salvati in memoria! Buona giornata")
        
        # Visualizzazione Grafica Semaforo
        if valore_calcolato <= 4.5:
            st.error(f" 🔴 BOLLINO ROSSO: {valore_calcolato}")
            st.write("La tua energia stimata è bassa oggi: cerca di delegare o posticipare qualche attività per non sovraccaricarti. 💪")
        elif valore_calcolato <= 7.0:
            st.warning(f" 🟡 BOLLINO GIALLO: {valore_calcolato}")
            st.write("Giornata regolare. Procedi con calma e ascolta il tuo corpo. 🌼")
        else:
            st.success(f" 🟢 BOLLINO VERDE: {valore_calcolato}")
            st.write("Ottimo! Hai una buona carica per affrontare la giornata con serenità. ✨")


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
                    st.success("✅ Dati registrati con successo nel tuo diario! Buona notte e sogni d'oro! 🌟")
                    st.session_state.mattina_salvata = False 
                else:
                    st.error(f"❌ Errore di salvataggio (Codice HTTP {r.status_code}). Verifica la configurazione dei campi.")
            except Exception as e:
                st.error(f"⚠️ Impossibile raggiungere Google Moduli: {e}")
