import streamlit as st
import requests
from datetime import datetime

# 1. Configurazione iniziale della pagina Streamlit
st.set_page_config(page_title="Sandbox di Sviluppo", page_icon="🔋", layout="centered")
st.title("Un altro giorno 🔋 - Sandbox di Sviluppo & Test")

# 2. URL esatto del tuo NUOVO Google Modulo di test
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSdtqnrzl71uqLgb1-wY5yw3R2vo7m8-nSwGgNf7ZtbrchqlYw/formResponse"

# 3. Creazione dei due Tab per dividere Mattina e Sera
tab_mattina, tab_sera = st.tabs(["☀️ Mattina: Predizione", "🌙 Sera: Riscontro"])


# --- ☀️ SCHEDA MATTINA ---
with tab_mattina:
    st.subheader("Compilazione Mattutina")
    
    # Creiamo un form grafico per i dati del mattino
    with st.form("form_mattina"):
        data_sel = st.date_input("Data", datetime.today())
        # Google vuole la data in formato GG/MM/AAAA
        data_formattata = data_sel.strftime("%d/%m/%Y")
        
        posizione = st.text_input("Posizione", value="Casa")
        temperatura = st.slider("Temperatura percepita", min_value=-10, max_value=50, value=20)
        sonno = st.selectbox("Qualità del sonno", ["ottima", "buona", "discreta", "insufficiente"])
        dolore = st.slider("Livello di dolore (0-10)", min_value=0, max_value=10, value=0)
        contesto = st.selectbox("Contesto", ["ufficio", "casa", "vacanza", "altro"])
        passi = st.selectbox("Previsione passi", ["fino a 1000", "1000-5000", "5000-10000", "oltre 10000"])
        bollino = st.selectbox("Bollino / Predizione", ["1", "2", "3"])
        
        # 🔥 NUOVA VARIABILE: Impatto del Caldo
        variabile_caldo = st.slider("Variabile Caldo (Livello fastidio da 1 a 5)", min_value=1, max_value=5, value=1)
        
        # Pulsante di invio della mattina
        invia_mattina = st.form_submit_button("Invia Predizione Mattutina 📤")
        
        if invia_mattina:
            # Pacchetto dati con i NUOVI ID del modulo accoppiati alle variabili di Streamlit
            dati_mattina = {
                "entry.2022449610": data_formattata,
                "entry.1412086707": posizione,
                "entry.1900939990": temperatura,
                "entry.2076355969": sonno,
                "entry.1596414247": dolore,
                "entry.1595201387": contesto,
                "entry.28384771": passi,
                "entry.625659299": bollino,
                "entry.672372933": variabile_caldo  # Invio della nuova variabile
            }
            
            try:
                risposta = requests.post(URL_MODULO, data=dati_mattina)
                if risposta.status_code == 200:
                    st.success("Dati del mattino inviati con successo al modulo di test! 🎉")
                    st.balloons()
                else:
                    st.error(f"Errore di invio. Codice risposta: {risposta.status_code}")
            except Exception as e:
                st.error(f"Si è verificato un errore di rete: {e}")


# --- 🌙 SCHEDA SERA ---
with tab_sera:
    st.subheader("Riscontro Serale")
    
    # Creiamo un form grafico separato per i dati della sera
    with st.form("form_sera"):
        data_sel_sera = st.date_input("Data del riscontro", datetime.today())
        data_formattata_sera = data_sel_sera.strftime("%d/%m/%Y")
        
        valutazione_predizione = st.selectbox(
            "Valutazione Predizione", 
            ["Match", "Overestimated", "Underestimated"]
        )
        note_serali = st.text_area("Note della sera", placeholder="Scrivi qui com'è andata davvero la giornata...")
        
        # Pulsante di invio della sera
        invia_sera = st.form_submit_button("Invia Riscontro Serale 🌙")
        
        if invia_sera:
            # Pacchetto dati della sera (inviamo solo la data per il match e i due campi serali)
            dati_serali = {
                "entry.2022449610": data_formattata_sera,
                "entry.375319797": valutazione_predizione,
                "entry.158362423": note_serali
            }
            
            try:
                risposta = requests.post(URL_MODULO, data=dati_serali)
                if risposta.status_code == 200:
                    st.success("Riscontro serale registrato! Buona serata! 🎈")
                    st.balloons()
                else:
                    st.error(f"Errore di invio. Codice risposta: {risposta.status_code}")
            except Exception as e:
                st.error(f"Si è verificato un errore di rete: {e}")
