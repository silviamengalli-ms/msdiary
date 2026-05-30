import streamlit as st
import requests
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAZIONE AMBIENTE DI TEST (Branch Sviluppo)
# ==============================================================================
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSdtqnrzl71uqLgb1-wY5yw3R2vo7m8-nSwGgNf7ZtbrchqlYw/formResponse"

ENTRY_IDS = {
    "data": "entry.2022449610",
    "posizione": "entry.1412086707",
    "temperatura": "entry.1900939990",
    "qualita_sonno": "entry.2076355969",
    "energia_risveglio": "entry.1596414247",
    "attivita": "entry.1595201387",
    "passi": "entry.28384771",
    "dolore": "entry.672372933",
    "semaforo": "entry.625659299",
    "note": "entry.158362423",
    "valutazione_predizione": "entry.375319797"
}

# ==============================================================================
# 2. DIZIONARI DEI PESI ALGORITMO
# ==============================================================================
PESI_SONNO = {
    "ottimo": 1.0,
    "soddisfacente": 0.5,
    "insufficiente": -0.5,
    "pessimo": -1.5
}

PESI_PASSI = {
    "fino a 1000": 0.0,
    "1000 - 3000": -0.3,
    "3000 - 5000": -0.7,
    "oltre 5000": -1.5
}

PESI_ATTIVITA = {
    "riposo totale": 0.5,
    "lavoro da casa": -0.2,
    "ufficio": -0.6,
    "piccole commissioni": -0.3,
    "fisioterapia/visite": -0.5,
    "impegno sociale": -0.4
}

# ==============================================================================
# 3. INTERFACCIA STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Un altro giorno - Sviluppo", page_icon="🔋", layout="centered")

st.title("Un altro giorno 🔋")
st.subheader("Sandbox di Sviluppo & Test")
st.caption("Stai lavorando sul codice parallelo collegato al database di TEST.")

# Divisione in Tab per Mattina e Sera
tab_mattina, tab_sera = st.tabs(["☀️ Mattina: Predizione", "🌙 Sera: Riscontro"])

# ------------------------------------------------------------------------------
# TAB MATTINA: CALCOLO E PREDIZIONE
# ------------------------------------------------------------------------------
with tab_mattina:
    st.header("Pianificazione Mattutina")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_oggi = st.date_input("Data", datetime.today())
        posizione = st.text_input("Posizione attuale", "Verona")
        energia = st.slider("Energia al risveglio (1-10)", 1, 10, 5)
        sonno = st.selectbox("Com'è andato il sonno?", list(PESI_SONNO.keys()))
        dolore = st.slider("Livello di dolore percepito (0-10)", 0, 10, 2)
        
    with col2:
        # Gestione Temperatura con slider per facilitare i test sul caldo
        temp_prevista = st.slider("Temperatura massima prevista (°C)", 15.0, 40.0, 24.0, step=0.5)
        attivita_scelte = st.multiselect("Attività pianificate", list(PESI_ATTIVITA.keys()), default=["riposo totale"])
        passi_stimati = st.selectbox("Stima dei passi", list(PESI_PASSI.keys()))

    # --- CORE LOGIC: CALCOLO DEL PUNTEGGIO MATEMATICO ---
    base_score = 3.0
    score_energia = energia * 0.4
    score_sonno = PESI_SONNO[sonno]
    score_passi = PESI_PASSI[passi_stimati]
    score_attivita = sum([PESI_ATTIVITA[att] for att in attivita_scelte])
    
    # Nuova Logica Scaglioni Caldo
    malus_caldo = 0.0
    if temp_prevista > 30.0:
        malus_caldo = -1.0
    elif temp_prevista > 28.0:
        malus_caldo = -0.5
        
    # Calcolo Finale
    punteggio_finale = base_score + score_energia + score_sonno + score_passi + score_attivita + malus_caldo
    
    # Limitiamo il punteggio in un range realistico tra 1 e 10
    punteggio_finale = max(1.0, min(10.0, punteggio_finale))

    # --- DETERMINAZIONE DEL BOLLINO ---
    if punteggio_finale >= 6.5:
        colore_bollino = "🟢 VERDE"
        messaggio_guida = "Ottime condizioni generali. Puoi procedere con i piani!"
        st.success(f"**Predizione: {colore_bollino}** (Punteggio stimato: {punteggio_finale:.1f})")
    elif punteggio_finale >= 4.5:
        colore_bollino = "🟡 GIALLO"
        messaggio_guida = "Attenzione alle energie residue. Valuta di alleggerire il pomeriggio."
        st.warning(f"**Predizione: {colore_bollino}** (Punteggio stimato: {punteggio_finale:.1f})")
    else:
        colore_bollino = "🔴 ROSSO"
        messaggio_guida = "Riserve energetiche in zona critica. Priorità assoluta al riposo."
        st.error(f"**Predizione: {colore_bollino}** (Punteggio stimato: {punteggio_finale:.1f})")
        
    st.info(f"💡 **Guida del Giorno:** {messaggio_guida}")
    
    # Visualizzazione dei dettagli dei pesi per debug nello sviluppo
    with st.expander("🔍 Ispeziona i pesi matematici applicati (Debug)"):
        st.write(f"Base: `{base_score}`")
        st.write(f"Fattore Energia (*0.4): `+{score_energia:.1f}`")
        st.write(f"Impatto Sonno: `{score_sonno}`")
        st.write(f"Impatto Attività: `{score_attivita:.1f}`")
        st.write(f"Impatto Passi: `{score_passi}`")
        st.write(f"Malus Caldo applicato: `{malus_caldo}` (Soglia impostata: >28°C: -0.5, >30°C: -1.0)")

    # Invio dati della Mattina
    if st.button("Invia Predizione Mattutina 📤", key="btn_mattina"):
        payload = {
            ENTRY_IDS["data"]: data_oggi.strftime("%Y-%m-%d"),
            ENTRY_IDS["posizione"]: posizione,
            ENTRY_IDS["temperatura"]: str(temp_prevista),
            ENTRY_IDS["qualita_sonno"]: sonno,
            ENTRY_IDS["energia_risveglio"]: str(energia),
            ENTRY_IDS["attivita"]: ", ".join(attivita_scelte),
            ENTRY_IDS["passi"]: passi_stimati,
            ENTRY_IDS["dolore"]: str(dolore),
            ENTRY_IDS["semaforo"]: colore_bollino,
            ENTRY_IDS["note"]: "Inserimento mattutino automatico.",
            ENTRY_IDS["valutazione_predizione"]: "" # Vuoto la mattina
        }
        
        try:
            response = requests.post(URL_MODULO, data=payload)
            if response.status_code == 200:
                st.balloons()
                st.success("Dati inviati con successo alla sandbox di test!")
            else:
                st.error(f"Errore di invio. Codice risposta: {response.status_code}")
        except Exception as e:
            st.error(f"Errore di connessione: {e}")

# ------------------------------------------------------------------------------
# TAB SERA: RISCONTRO E VERIFICA PREDIZIONE
# ------------------------------------------------------------------------------
with tab_sera:
    st.header("Consuntivo Serale")
    st.write("Usa questa sezione a fine giornata per registrare com'è andata davvero e calibrare l'algoritmo.")
    
    data_sera = st.date_input("Data Riscontro", datetime.today(), key="data_sera")
    
    # La nuova colonna pulita creata nel Google Modulo
    valutazione = st.selectbox(
        "Come valuti la predizione fatta dall'app questa mattina?",
        ["Match", "Overestimated (L'app ha sovrastimato le mie energie)", "Underestimated (L'app ha sottostimato le mie energie)"]
    )
    
    note_serali = st.text_area("Note serali (Sintomi, variazioni di programma, riflessioni):", placeholder="Es. #sintomi: parestesia, stanchezza improvvisa ore 16:00")
    
    if st.button("Invia Riscontro Serale 💾", key="btn_sera"):
        payload_sera = {
            ENTRY_IDS["data"]: data_sera.strftime("%Y-%m-%d"),
            ENTRY_IDS["valutazione_predizione"]: valutazione,
            ENTRY_IDS["note"]: note_serali,
            # Lasciamo vuoti o di default i campi della mattina per non sovrascrivere la logica delle righe
            ENTRY_IDS["posizione"]: "Consuntivo Serale",
            ENTRY_IDS["temperatura"]: "",
            ENTRY_IDS["qualita_sonno"]: "",
            ENTRY_IDS["energia_risveglio"]: "",
            ENTRY_IDS["attivita"]: "",
            ENTRY_IDS["passi"]: "",
            ENTRY_IDS["dolore"]: "",
            ENTRY_IDS["semaforo"]: ""
        }
        
        try:
            response = requests.post(URL_MODULO, data=payload_sera)
            if response.status_code == 200:
                st.success("Riscontro serale registrato! Ottimo per lo storico calibrazione.")
            else:
                st.error(f"Errore di invio. Codice: {response.status_code}")
        except Exception as e:
            st.error(f"Errore: {e}")
