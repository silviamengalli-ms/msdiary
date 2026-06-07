import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
import plotly.express as px

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="La Mia Carica - MS Diary", layout="centered", page_icon="🔋")

# URL DI INVIO DATI (Punta al formResponse del modulo)
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

# URL CONFIGURATO CON IL TUO FOGLIO GOOGLE REALE
URL_FOGLIO_DATI = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv"

# MAPPATURA DEI NOMI DELLE COLONNE SUL TUO FOGLIO GOOGLE
# Se l'app ti segnala un errore, verifica che questi testi corrispondano esattamente alle intestazioni delle colonne del foglio!
COLONNE_FOGLIO = {
    'data': '🗓️ Data:',                          # Es. 'Informazioni cronologiche' oppure il nome della tua domanda sulla data
    'energia': '⚡ Energia al risveglio (1-10):', 
    'dolore': 'Livello dolore avvertito (1-10):', 
    'semaforo': 'Semaforo'                        
}

# MAPPATURA INPUT GOOGLE MODULI
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
    'siesta_form': 'entry.1353678088', 
    'dolore': 'entry.672372933',
    'valutazione': 'entry.2023032977',
    'note': 'entry.158362423'
}

# --- STATO INIZIALE (Inizializzazione Sicura della memoria) ---
stato_iniziale = {
    'mattina_salvata': False,
    'mattina_data': None, 
    'posizione': 'Verona',
    'temp': 20.0, 
    'umidita': 50, 
    'sonno': 'discreta', 
    'passi': 'da 1001 a 3000', 
    'energia': 5, 
    'attivita': [], 
    'siesta': False,  
    'valore_sem': None
}

for chiave, valore in stato_iniziale.items():
    if chiave not in st.session_state:
        st.session_state[chiave] = valore

# --- FUNZIONE RE-TRY LOGIC ---
def invia_richiesta_con_riconnessione(url, parametri):
    for tentativo in range(3): 
        try:
            risposta = requests.get(url, params=parametri, timeout=5)
            if risposta.status_code == 200: return risposta 
            elif risposta.status_code == 429:
                time.sleep(random.uniform(0.5, 2.0))
                continue
            else: return risposta
        except requests.exceptions.RequestException:
            time.sleep(random.uniform(0.5, 2.0))
    return None

# --- FUNZIONE METEO ---
@st.cache_data(ttl=60)
def recupera_meteo(data, nome_citta):
    try:
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"
        params_geo = {"name": nome_citta.strip(), "count": 1, "language": "it", "format": "json"}
        risposta_geo = invia_richiesta_con_riconnessione(url_geo, params_geo)
        if not risposta_geo or risposta_geo.status_code != 200: return 20.0, 50, "Errore di rete"
        data_geo = risposta_geo.json()
        lat, lon = 45.43, 10.99
        if "results" in data_geo and len(data_geo["results"]) > 0:
            lat = data_geo["results"][0]["latitude"]
            lon = data_geo["results"][0]["longitude"]
        else: return 20.0, 50, f"Città non trovata."
        d_str = data.strftime("%Y-%m-%d")
        url_meteo = "https://api.open-meteo.com/v1/forecast"
        params_meteo = {"latitude": lat, "longitude": lon, "start_date": d_str, "end_date": d_str, "daily": "temperature_2m_max", "hourly": "relative_humidity_2m", "timezone": "Europe/Rome"}
        risposta_meteo = invia_richiesta_con_riconnessione(url_meteo, params_meteo)
        if not risposta_meteo or risposta_meteo.status_code != 200: return 20.0, 50, "Errore di rete"
        resp = risposta_meteo.json()
        val_temp = float(resp['daily']['temperature_2m_max'][0])
        umidita_orarie = resp['hourly']['relative_humidity_2m']
        val_umidita = int(sum(umidita_orarie) / len(umidita_orarie))
        return val_temp, val_umidita, None
    except Exception as e: return 20.0, 50, str(e)

# --- INTERFACCIA UTENTE ---
st.title("🔋 La Mia Carica")
st.markdown("---")

# Creazione dei 3 TAB
tab_mattina, tab_sera, tab_stats = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale", "📊 Statistiche & Trend"])

# ==========================================
# TAB MATTINA
# ==========================================
with tab_mattina:
    col1, col2 = st.columns(2)
    with col1:
        data_sel = st.date_input("🗓️ Data:", value=datetime.date.today(), format="DD/MM/YYYY")
        posizione_input = st.text_input("📍 Posizione:", value=st.session_state.posizione)
    temp_api, umidita_api, errore_rilevato = recupera_meteo(data_sel, posizione_input)
    with col2:
        temp = st.number_input("🌡️ Temperatura massima prevista per oggi (°C):", value=temp_api)
        umidita = st.number_input("💧 Umidità media prevista (%):", value=int(umidita_api))
    if errore_rilevato: st.warning("⚠️ Centralina meteo sovraccarica. Aggiorna o compila a mano.")
    st.markdown("---") 
    sonno = st.selectbox("💤 Qualità del sonno:", ["discreta", "soddisfacente", "scarsa"])
    passi = st.selectbox("🚶 Passi previsti:", ["fino a 1000", "da 1001 a 3000", "oltre 3000"])
    energia = st.slider("⚡ Energia al risveglio (1-10):", 1, 10, 5)
    siesta = st.checkbox("🛌 Pianifico una siesta strategica/efficace oggi", value=st.session_state.siesta)
    attivita = st.multiselect("📅 Attività in programma:", ["ufficio", "lavoro da casa", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        pesi = {"ufficio": -0.5, "lavoro da casa": -0.2, "piccole commissioni": -0.4, "visita": -0.5, "fisioterapia": -0.5, "riposo totale": 0.5, "sociale": -0.7}
        somma_att = sum([pesi[a] for a in attivita])
        if len(attivita) > 1: somma_att += (len(attivita) - 1) * -0.3
        p_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3)
        peso_sonno = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}[sonno]
        peso_passi = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre 3000": -0.3}[passi]
        
        score = 5.0 + (energia * 0.3) + peso_sonno + peso_passi + somma_att + p_temp
        if siesta: score += 0.3
        valore_calcolato = round(max(1.0, min(10.0, score)), 1)
        
        st.session_state.update({'mattina_salvata': True, 'mattina_data': data_sel, 'posizione': posizione_input, 'temp': temp, 'umidita': umidita, 'sonno': sonno, 'passi': passi, 'energia': energia, 'attivita': attivita, 'siesta': siesta, 'valore_sem': valore_calcolato})
        st.markdown("---") 
        if valore_calcolato <= 4.5: st.error(f"🔴 BOLLINO ROSSO: {valore_calcolato} Dai priorità al riposo 🐢")
        elif valore_calcolato <= 7.0: st.warning(f"🟡 BOLLINO GIALLO: {valore_calcolato} Giornata regolare, procedi con calma 🐘")
        else: st.success(f"🟢 BOLLINO VERDE: {valore_calcolato} Ottima carica! 🦋")
        st.write("✅ Dati salvati in memoria! Compila il feedback stasera.")

# ==========================================
# TAB SERA
# ==========================================
with tab_sera:
    if not st.session_state.mattina_salvata:
        st.warning("⚠️ Compila e salva prima i dati del mattino nella scheda precedente!")
    else:
        st.subheader("Com'è andata la giornata?")
        st.markdown(f"Punteggio stimato stamattina: **{st.session_state.valore_sem}**")
        valutazione = st.selectbox("Il punteggio del mattino era corretto? (Riscontro):", ["Match", "Overestimated", "Underestimated"])
        dolore = st.slider("Livello dolore avvertito (1-10):", 1, 10, 1)
        note = st.text_area("Note o riflessioni serali:", placeholder="Scrivi qui le tue annotazioni...")
        
        if st.button("💾 REGISTRA IL MIO DIARIO", use_container_width=True):
            stringa_attivita_completa = ", ".join(st.session_state.attivita) if st.session_state.attivita else "Nessuna"
            note_finali = f"[Attività svolte: {stringa_attivita_completa}] {note}".strip()
            semaforo_protetto = max(1, min(10, int(round(st.session_state.valore_sem))))
            
            payload = {
                ENTRY_ID['data']: st.session_state.mattina_data.strftime("%d/%m/%Y"), ENTRY_ID['posizione']: st.session_state.posizione,
                ENTRY_ID['temp']: str(int(round(st.session_state.temp))), ENTRY_ID['umidita']: str(int(st.session_state.umidita)),
                ENTRY_ID['sonno']: st.session_state.sonno, ENTRY_ID['energia']: str(int(st.session_state.energia)),
                ENTRY_ID['passi']: st.session_state.passi, ENTRY_ID['semaforo']: str(semaforo_protetto),
                ENTRY_ID['siesta_form']: "si" if st.session_state.siesta else "no", ENTRY_ID['valutazione']: valutazione,
                ENTRY_ID['dolore']: str(int(dolore)), ENTRY_ID['note']: note_finali
            }
            if st.session_state.attivita: payload[ENTRY_ID['attivita']] = st

# ==========================================
# TAB STATISTICHE (Versione Ottimizzata: Mattina vs Sera)
# ==========================================
with tab_stats:
    st.subheader("📊 Consapevolezza del Diario: Previsione vs Vissuto")
    
    try:
        df = pd.read_csv(URL_FOGLIO_DATI)
        
        if df.empty:
            st.warning("Il database è ancora vuoto. Registra qualche giornata per sbloccare l'analisi!")
        else:
            st.success(f"📈 Sincronizzato! Analisi basata su {len(df)} giornate registrate.")
            
            # Mappatura delle colonne reali del tuo foglio
            col_data = "Data"
            col_energia = "Energia al risveglio"
            col_riscontro = "riscontro"
            
            # --- 1. ANALISI DELL'AFFIDABILITÀ DEI BOLLINI (RISCONTRO) ---
            st.markdown("### 🎯 Quante volte la previsione del mattino era corretta?")
            st.markdown("*Questo grafico mostra quanto la stima del mattino ha rispecchiato la tua giornata reale secondo i tuoi feedback serali.*")
            
            if col_riscontro in df.columns:
                # Pulizia del dato (rimuove spazi bianchi)
                df[col_riscontro] = df[col_riscontro].astype(str).str.strip()
                
                conteggio_riscontri = df[col_riscontro].value_counts().reset_index()
                conteggio_riscontri.columns = ['Giudizio Serale', 'Giorni']
                
                # Creazione del grafico a torta basato sul vissuto della sera
                fig_riscontro = px.pie(
                    conteggio_riscontri, 
                    names='Giudizio Serale', 
                    values='Giorni',
                    color='Giudizio Serale',
                    color_discrete_map={
                        'Match': '#00c853',           # Verde: Previsione azzeccata
                        'Overestimated': '#ff4b4b',   # Rosso: La giornata è stata più faticosa del previsto
                        'Underestimated': '#ffa500'   # Arancione: La giornata è andata meglio del previsto
                    },
                    hole=0.4
                )
                st.plotly_chart(fig_riscontro, use_container_width=True)
            else:
                st.error(f"Non trovo la colonna '{col_riscontro}' nel foglio.")

            st.markdown("---")

            # --- 2. ANDAMENTO DELL'ENERGIA MATTUTINA ---
            st.markdown("### 📈 Andamento dell'Energia al Risveglio")
            st.markdown("*Monitora come fluttua la tua carica iniziale giorno dopo giorno.*")
            
            if col_data in df.columns and col_energia in df.columns:
                df_energia = df[[col_data, col_energia]].copy()
                df_energia[col_energia] = pd.to_numeric(df_energia[col_energia], errors='coerce')
                
                # Rinominiamo la colonna per l'interfaccia grafico
                df_energia.columns = ['Data', 'Energia al Mattino']
                
                # Grafico lineare dell'energia
                st.line_chart(df_energia.set_index('Data'))
                st.caption("Tracciando solo l'energia, puoi osservare se ci sono cicli o pattern ripetitivi nei tuoi risvegli.")
            else:
                st.error("Verifica la presenza delle colonne Data ed Energia nel tuo foglio.")
                
    except Exception as e:
        st.error(f"⚠️ Errore nel caricamento dei grafici: {e}")
