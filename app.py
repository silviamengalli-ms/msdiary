import streamlit as st
import pandas as pd
import datetime
import requests

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="MS Diary - Predizione", page_icon="📊", layout="centered")

# --- ACCOPPIAMENTO GOOGLE (DATI REALI) ---
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

ENTRY_ID = {
    'posizione': 'entry.1412086707',
    'temp': 'entry.1900939990',
    'sonno': 'entry.2076355969',
    'energia': 'entry.1596414247',
    'attivita': 'entry.1595201387',
    'semaforo': 'entry.625659299',
    'dolore': 'entry.672372933',
    'passi': 'entry.28384771',
    'note': 'entry.158362423'
}

URL_FOGLIO_CSV = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# --- PARAMETRI LOGICA AI (PESI FISSI) ---
PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre 3000": -0.5}
PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.1, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.4, "riposo totale": 0.5, "sociale": -0.7
}

def recupera_meteo_automatico(data_target):
    try:
        data_str = data_target.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        response = requests.get(url_meteo)
        return float(response.json()['daily']['temperature_2m_max'][0])
    except:
        return 20.0

# --- INTERFACCIA UTENTE ---
st.title("📊 Il Mio Diario & Predittore")

col1, col2 = st.columns(2)
with col1:
    posizione = st.text_input("📍 Luogo:", value="Verona")
    temp = st.number_input("Temperatura (°C)", value=recupera_meteo_automatico(datetime.date.today()))
    sonno = st.selectbox("Sonno", ["discreta", "soddisfacente", "scarsa"])
    energia = st.slider("Energia al risveglio (1-10):", 1, 10, 5)
with col2:
    passi = st.selectbox("Passi", ["fino a 1000", "da 1001 a 3000", "oltre 3000"])
    attivita = st.multiselect("Attività", ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])
    dolore = st.slider("Dolore (1-10 - dato background):", 1, 10, 1)

# --- CALCOLO PREDIZIONE ---
st.markdown("---")
st.subheader("🔮 Stato del Semaforo")

if st.button("🔄 Calcola Predizione AI"):
    score = 3.0 + (energia * 0.4)
    score += PESI_SONNO.get(sonno, 0)
    score += PESI_PASSI.get(passi, 0)
    score += sum([PESI_ATTIVITA.get(a, 0) for a in attivita])
    
    if "riposo totale" not in attivita:
        if temp > 30: score -= 2.0 
        elif 20 < temp <= 30: score -= 0.8 
    elif "riposo totale" in attivita and temp > 30:
        score -= 0.3 
        
    st.session_state['semaforo_predetto'] = round(max(1.0, min(10.0, score)), 1)

# Recupero del valore predizione
valore_calcolato = st.session_state.get('semaforo_predetto', 5.0)

if valore_calcolato <= 5: 
    st.error(f"Stato predetto: ROSSO (Valore calcolato: {valore_calcolato})")
elif 6 <= valore_calcolato <= 8: 
    st.warning(f"Stato predetto: GIALLO (Valore calcolato: {valore_calcolato})")
else: 
    st.success(f"Stato predetto: VERDE (Valore calcolato: {valore_calcolato})")

# --- SEZIONE DIARIO / SERALE ---
st.markdown("---")
st.subheader("📝 Note & Validazione Serale")

feedback = st.selectbox("Feedback sul predittore:", ["#Match", "#Overestimate", "#Underestimate"])

st.info("""
**🏷️ Tag suggeriti per le tue note:**
* **#Sintomo:** (es. #sintomo: brainfog)
* **#Farmaco:** (es. #farmaco: integratore)
* **#Clima:** (es. #clima: umido)
* **#AttivitàExtra:** (es. #attivitàextra: spesa)
""")

note_input = st.text_area("Descrivi la giornata usando i tag:")

# --- INVIO DATI ---
if st.button("💾 Registra Giornata Definitiva", type="primary"):
    if note_input.strip():
        note_complete = f"{feedback} | {note_input}"
    else:
        note_complete = feedback
    
    # Costruzione payload identica al backup funzionante
    payload = {
        ENTRY_ID['posizione']: posizione,
        ENTRY_ID['temp']: str(int(temp)),
        ENTRY_ID['sonno']: sonno,
        ENTRY_ID['energia']: str(energia),
        ENTRY_ID['dolore']: str(dolore), 
        ENTRY_ID['semaforo']: str(int(round(valore_calcolato))),
        ENTRY_ID['passi']: passi,
        ENTRY_ID['note']: note_complete
    }
    
    payload_lista = list(payload.items())
    for a in attivita:
        payload_lista.append((ENTRY_ID['attivita'], a))
    
    try:
        response = requests.post(URL_MODULO, data=payload_lista)
        if response.status_code == 200: 
            st.success("🎉 Registrazione riuscita con successo!")
        else: 
            st.error(f"Errore {response.status_code}: Il modulo ha rifiutato i dati.")
            
            # --- ISPETTORE DIAGNOSTICO ---
            st.write("### 🔍 Ispettore Dati (Cosa stiamo inviando a Google):")
            st.warning("Confronta questi valori con le opzioni reali sul tuo Modulo Google per trovare l'errore (es. controlla maiuscole/minuscole o campi obbligatori lasciati vuoti):")
            st.write(payload_lista)
            
    except Exception as e:
        st.error(f"Errore connessione: {e}")
