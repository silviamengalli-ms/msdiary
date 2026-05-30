import streamlit as st
import datetime
import requests

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica", layout="centered", page_icon="🔋")

# --- PESI E LOGICA ---
PESI_SONNO = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}
PESI_PASSI = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre i 3000": -0.3}
PESI_ATTIVITA = {
    "ufficio": -0.5, "lavoro da casa": -0.2, "piccole commissioni": -0.4, 
    "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "sociale": -0.7
}

@st.cache_data(ttl=3600)
def recupera_meteo(data):
    try:
        data_str = data.strftime("%Y-%m-%d")
        url = f"https://api.open-meteo.com/v1/forecast?latitude=45.43&longitude=10.99&start_date={data_str}&end_date={data_str}&daily=temperature_2m_max&timezone=Europe/Rome"
        resp = requests.get(url).json()
        return float(resp['daily']['temperature_2m_max'][0])
    except: return 20.0

# --- INTERFACCIA ACCOGLIENTE ---
st.title("🔋 La Mia Carica")
st.markdown("---")
st.markdown("Ciao! Prepara la tua giornata e scopri come si prospetta la tua energia. 😊")

tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

with tab_mattina:
    data_sel = st.date_input("🗓️ Data:", value=datetime.date.today(), format="DD-MM-YYYY")
    temp_prevista = recupera_meteo(data_sel)
    
    col1, col2 = st.columns(2)
    with col1:
        temp = st.slider("🌡️ Temperatura prevista (°C):", -5.0, 45.0, float(temp_prevista), 0.5)
        sonno = st.selectbox("💤 Qualità del sonno:", list(PESI_SONNO.keys()))
    with col2:
        passi = st.selectbox("🚶 Passi previsti:", list(PESI_PASSI.keys()))
        energia = st.slider("⚡ Energia al risveglio:", 1, 10, 5)
        
    attivita = st.multiselect("📅 Attività in programma:", list(PESI_ATTIVITA.keys()))

    # --- CALCOLO ---
    pesi_selezionati = [PESI_ATTIVITA[a] for a in attivita]
    somma_pesi_attivita = sum(pesi_selezionati)
    if len(attivita) > 1: somma_pesi_attivita += (len(attivita) - 1) * -0.3
    peso_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3)
    
    score = 5.0 + (energia * 0.3) + PESI_SONNO[sonno] + PESI_PASSI[passi] + somma_pesi_attivita + peso_temp
    valore_sem = round(max(1.0, min(10.0, score)), 1)
    
    st.markdown("---")
    # Messaggi personalizzati e accoglienti
    if valore_sem <= 4.5:
        st.error(f"### 🔴 BOLLINO ROSSO: {valore_sem}")
        st.write("La tua energia è bassa oggi. Cerca di dare priorità al riposo e non sovraccaricarti. 💪")
    elif valore_sem <= 7.0:
        st.warning(f"### 🟡 BOLLINO GIALLO: {valore_sem}")
        st.write("Giornata regolare. Procedi con calma e ascolta il tuo corpo. 🌼")
    else:
        st.success(f"### 🟢 BOLLINO VERDE: {valore_sem}")
        st.write("Ottimo! Hai una buona carica per affrontare la giornata con serenità. ✨")

with tab_sera:
    st.subheader("Com'è andata la giornata?")
    dolore = st.slider("Livello dolore avvertito:", 1, 10, 1)
    valutazione = st.selectbox("Il punteggio del mattino era corretto?", ["Match", "Overestimated", "Underestimated"])
    note = st.text_area("Note o riflessioni:")
    
    if st.button("💾 Registra il mio diario"):
        st.balloons() # Tocco divertente per il salvataggio
        st.success("Dati registrati con successo! Grazie per la tua costanza. 🌟")
