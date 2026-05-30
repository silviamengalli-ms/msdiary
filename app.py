import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - Diario Energetico", layout="centered")

# Aggiornato con l'URL del tuo NUOVO modulo
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSdtqnrzl71uqLgb1-wY5yw3R2vo7m8-nSwGgNf7ZtbrchqlYw/formResponse"

ENTRY_ID = {
    'data': 'entry.2022449610',
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'passi': 'entry.28384771',
    'note': 'entry.158362423',
    'valutazione_predizione': 'entry.375319797'
}

# Pesi matematici
PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.5}
PESI_ATTIVITA = {
    "ufficio": -0.5, 
    "lavoro da casa": -0.1, 
    "piccole commissioni": -0.4, 
    "visita": -0.5, 
    "fisioterapia": -0.4, 
    "riposo totale": 0.5, 
    "sociale": -0.7
}

# --- MEMORIA DI STATO ---
if 'valore_sem' not in st.session_state:
    st.session_state.valore_sem = None

def recupera_meteo(data):
    try:
        data_str = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0])
    except: 
        return 20.0

# --- INTERFACCIA PRINCIPALE ---
st.header("🔋 La Mia Carica")
st.markdown("##")

# Creazione dei due Tab per la scansione temporale della giornata
tab_mattina, tab_sera = st.tabs(["🌅 Mattina: Fase Previsionale", "🌌 Sera: Feedback & Registro"])

# --- TAB 1: MATTINA ---
with tab_mattina:
    st.markdown("#### *Buongiorno! Come ti senti stamattina?* 😊")
    st.markdown("Pianifichiamo la giornata e calcoliamo il tuo indice energetico previsto.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        data_sel = st.date_input("Seleziona la data di oggi:", value=datetime.date.today(), format="DD-MM-YYYY")
        posizione = st.text_input("Dove ti trovi? (Luogo):", value="Verona")
        temp = st.number_input("Temperatura massima prevista per oggi (°C):", value=recupera_meteo(data_sel))
        sonno = st.selectbox("Qualità del sonno dell'ultima notte:", list(PESI_SONNO.keys()))

    with col2:
        passi = st.selectbox("Quanti passi pensi di fare oggi?:", list(PESI_PASSI.keys()))
        attivita = st.multiselect("Attività in programma per oggi:", list(PESI_ATTIVITA.keys()))
        energia = st.slider("Energia al risveglio (1-10):", 1, 10, 5)

    st.markdown("---")
    
    if st.button("🔮 CALCOLA PREDIZIONE 🔮", use_container_width=True):
        somma_pesi_attivita = sum([PESI_ATTIVITA[a] for a in attivita])
        
        # --- 🌡️ SISTEMAZIONE PESO RELATIVO ALLA TEMPERATURA ---
        if temp <= 28.0:
            peso_temperatura = 0.0     # Verde: fino a 28 gradi nessun impatto
        elif 28.0 < temp <= 30.0:
            peso_temperatura = -0.5    # Giallo: dai 28 ai 30 gradi toglie 0.5
        else:
            peso_temperatura = -1.0    # Rosso: oltre i 30 gradi toglie 1.0
            
        # Calcolo finale con l'impatto della temperatura
        score = 3.0 + (energia * 0.4) + PESI_SONNO[sonno] + PESI_PASSI[passi] + somma_pesi_attivita + peso_temperatura
        st.session_state.valore_sem = round(max(1.0, min(10.0, score)), 1)

    if st.session_state.valore_sem is not None:
        if st.session_state.valore_sem <= 4.5:
            pallino = "🔴"
            testo_bollino = "BOLLINO ROSSO"
        elif st.session_state.valore_sem <= 7.0:
            pallino = "🟡"
            testo_bollino = "BOLLINO GIALLO"
        else:
            pallino = "🟢"
            testo_bollino = "BOLLINO VERDE"
            
        st.markdown(f"<p style='text-align: center; font-weight: bold;'>{pallino} {st.session_state.valore_sem} - {testo_bollino} {pallino}</p>", unsafe_allow_html=True)
        st.info("💡 Ora puoi passare alla scheda della **Sera** quando vuoi per aggiungere le note e registrare la giornata!")


# --- TAB 2: SERA ---
with tab_sera:
    st.markdown("#### *Buonasera! Com'è andata davvero oggi?* 🌙")
    st.markdown("Raccogliamo un ultimo feedback e salviamo i dati della giornata nel tuo diario.")
    st.markdown("---")
    
    col_sera1, col_sera2 = st.columns(2)
    with col_sera1:
        dolore = st.slider("Che livello di dolore o fastidio hai avvertito in generale? (1-10):", 1, 10, 1)
        
    with col_sera2:
        valutazione = st.selectbox(
            "Riscontro rispetto alla predizione del mattino:",
            ["Seleziona un'opzione...", "Match", "Overestimated", "Underestimated"]
        )
    
    st.markdown("##")
    st.markdown("<h3 style='text-align: center;'>💡 Note 💡</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'><code>#sintomi</code> &nbsp; <code>#clima</code> &nbsp; <code>#attivita_extra</code> &nbsp; <code>#umore</code></p>", unsafe_allow_html=True)

    note_input = st.text_area("Note aggiuntive:", label_visibility="collapsed", placeholder="Aggiungi qui qualsiasi annotazione libera o sintomo particolare della giornata...")

    st.markdown("---")

    if st.button("💾 REGISTRA GIORNATA", use_container_width=True):
        if st.session_state.valore_sem is None:
            st.error("⚠️ Attenzione: Devi prima calcolare il valore del Semaforo nella scheda '🌅 Mattina' prima di poter registrare!")
        else:
            stringa_attivita_completa = ", ".join(attivita) if attivita else "Nessuna"
            note_finali = f"[Attività svolte: {stringa_attivita_completa}] {note_input}".strip()
            
            payload = {
                ENTRY_ID['data']: data_sel.strftime("%d/%m/%Y"),
                ENTRY_ID['posizione']: posizione,
                ENTRY_ID['temp']: str(int(temp)),
                ENTRY_ID['sonno']: sonno,
                ENTRY_ID['energia']: str(energia),
                ENTRY_ID['passi']: passi,
                ENTRY_ID['dolore']: str(dolore),
                ENTRY_ID['semaforo']: str(int(round(st.session_state.valore_sem))),
                ENTRY_ID['note']: note_finali
            }
            
            if valutazione != "Seleziona un'opzione...":
                payload[ENTRY_ID['valutazione_predizione']] = valutazione
            else:
                payload[ENTRY_ID['valutazione_predizione']] = ""
            
            if attivita:
                payload[ENTRY_ID['attivita']] = attivita[0]
                
            try:
                r = requests.post(URL_MODULO, data=payload)
                if r.status_code == 200:
                    st.success("✅ Splendido! La tua giornata è stata registrata con successo.")
                    st.session_state.valore_sem = None
                else:
                    st.error(f"❌ Errore HTTP {r.status_code}. Il server ha rifiutato la richiesta.")
            except Exception as e:
                st.error(f"⚠️ Errore di connessione: {e}")
