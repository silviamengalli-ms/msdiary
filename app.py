import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PRINCIPALE ---
st.set_page_config(page_title="La Mia Carica - MS Diary", layout="centered", page_icon="🔋")

# URL DI INVIO DATI PRINCIPALE (formResponse)
URL_MODULO = "https://docs.google.com/forms/d/e/1FAIpQLSfsNrtCcCMKrQ22pM-7NfrW7F9xWvtUSZPNBu83AgV9ZyWtDQ/formResponse"

# MAPPATURA INPUT GOOGLE MODULI AGGIORNATA (MAIN)
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
    'note': 'entry.158362423',
    'crash': 'entry.592499523'
}

# --- STATO INIZIALE ---
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

# --- FUNZIONE INTERNA: CALCOLO DIRETTO DELLE 72 ORE DAL FOGLIO ---
def calcola_zavorra_72ore():
    try:
        # Connessione sicura nativa tramite i Secrets inseriti nella dashboard di Streamlit
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Legge il database in tempo reale (mantiene in cache per 5 minuti per efficienza)
        df = conn.read(ttl="5m") 
        
        if df is None or len(df) < 3:
            return 0.0, "Storico insufficiente nel database (< 3 righe)"
        
        # Identificazione automatica delle colonne per evitare problemi di maiuscole/minuscole
        colonna_crash = [c for c in df.columns if 'crash' in c.lower()]
        colonna_match = [c for c in df.columns if 'valutazione' in c.lower() or 'riscontro' in c.lower()]
        
        if not colonna_crash:
            return 0.0, "Nessuna zavorra attiva (In attesa dei primi dati con colonna Crash)"
            
        col_c = colonna_crash[0]
        col_m = colonna_match[0] if colonna_match else None
        
        # Isoliamo gli ultimi 3 giorni reali registrati nel file
        ultimi_3_giorni = df.tail(3).to_dict('records')
        ieri = ultimi_3_giorni[-1]
        due_giorni_fa = ultimi_3_giorni[-2]
        tre_giorni_fa = ultimi_3_giorni[-3]
        
        pesi_temporali = {'ieri': 1.0, 'due_giorni': 0.5, 'tre_giorni': 0.25}
        zavorra_totale = 0.0
        dettaglio_log = []
        
        # Analisi Ieri (Impatto 100%)
        val_crash_ieri = str(ieri.get(col_c, '0')).strip()
        if val_crash_ieri.startswith('1'):
            impatto = 1.5 * pesi_temporali['ieri']
            if col_m and str(ieri.get(col_m, '')).strip() == "Underestimated":
                impatto *= 1.5  # Moltiplicatore correttivo di protezione
            zavorra_totale += impatto
            dettaglio_log.append(f"Ieri (-{impatto})")

        # Analisi 2 Giorni Fa (Impatto 50%)
        val_crash_due = str(due_giorni_fa.get(col_c, '0')).strip()
        if val_crash_due.startswith('1'):
            impatto = 1.5 * pesi_temporali['due_giorni']
            if col_m and str(due_giorni_fa.get(col_m, '')).strip() == "Underestimated":
                impatto *= 1.5
            zavorra_totale += impatto
            dettaglio_log.append(f"2gg fa (-{impatto})")

        # Analisi 3 Giorni Fa (Impatto 25%)
        val_crash_tre = str(tre_giorni_fa.get(col_c, '0')).strip()
        if val_crash_tre.startswith('1'):
            impatto = 1.5 * pesi_temporali['tre_giorni']
            if col_m and str(tre_giorni_fa.get(col_m, '')).strip() == "Underestimated":
                impatto *= 1.5
            zavorra_totale += impatto
            dettaglio_log.append(f"3gg fa (-{impatto})")
            
        stringa_report = " + ".join(dettaglio_log) if dettaglio_log else "Nessun sovraccarico rilevato, corpo libero."
        return round(zavorra_totale, 2), stringa_report

    except Exception as e:
        return 0.0, f"In attesa del primo allineamento storico: {str(e)}"

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

tab_mattina, tab_sera = st.tabs(["🌅 Pianifica la Mattina", "🌌 Feedback Serale"])

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
    
    attivita = st.multiselect("📅 Attività in programma:", ["ufficio", "lavoro da casa", "studio", "piccole commissioni", "visita", "fisioterapia", "riposo totale", "sociale"])

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        # 1. RECUPERO DELLA ZAVORRA PREVENTIVA DAL PASSATO
        zavorra, log_zavorra = calcola_zavorra_72ore()
        
        pesi = {
            "ufficio": -0.5, "lavoro da casa": -0.2, "studio": -0.3, # Peso studio applicato stabilmente
            "piccole commissioni": -0.4, "visita": -0.5, "fisioterapia": -0.5, 
            "riposo totale": 0.5, "sociale": -0.7
        }
        
        somma_att = sum([pesi[a] for a in attivita])
        if len(attivita) > 1: somma_att += (len(attivita) - 1) * -0.3
        p_temp = 0.0 if temp < 28.0 else -0.5 - ((temp - 28.0) * 0.3)
        peso_sonno = {"discreta": 0.0, "soddisfacente": 1.0, "scarsa": -1.5}[sonno]
        peso_passi = {"fino a 1000": 0.5, "da 1001 a 3000": 0.0, "oltre 3000": -0.3}[passi]
        
        # Algoritmo base odierno
        score = 5.0 + (energia * 0.3) + peso_sonno + peso_passi + somma_att + p_temp
        if siesta: score += 0.3
        
        # 2. APPLICAZIONE DELLO SCUDO DELLE 72 ORE
        score_finale = score - zavorra
        valore_calcolato = round(max(1.0, min(10.0, score_finale)), 1)
        
        st.session_state.update({'mattina_salvata': True, 'mattina_data': data_sel, 'posizione': posizione_input, 'temp': temp, 'umidita': umidita, 'sonno': sonno, 'passi': passi, 'energia': energia, 'attivita': attivita, 'siesta': siesta, 'valore_sem': valore_calcolato})
        
        st.markdown("---") 
        # Notifica visiva dello scudo zavorra
        if zavorra > 0:
            st.warning(f"🛡️ **Scudo 72 Ore Attivo**: Il punteggio iniziale è stato ridotto preventivamente di **-{zavorra} punti** per sovraccarichi passati. ({log_zavorra})")
        else:
            st.caption(f"📊 Controllo Storico: {log_zavorra}")
            
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
        
        # Selettore Serale del Crash
        crash_scelta = st.radio(
            "💥 C'è stato un crash/sovraccarico oggi?", 
            ["0 - No", "1 - Sì"], 
            index=0, 
            horizontal=True
        )
        
        valutazione = st.selectbox("Il punteggio del mattino era corretto? (Riscontro):", ["Match", "Overestimated", "Underestimated"])
        dolore = st.slider("Livello dolore avvertito (1-10):", 1, 10, 1)
        note = st.text_area("Note o riflessioni serali:", placeholder="Scrivi qui le tue annotazioni...")
        
        if st.button("💾 REGISTRA IL MIO DIARIO", use_container_width=True):
            stringa_attivita_completa = ", ".join(st.session_state.attivita) if st.session_state.attivita else "Nessuna"
            note_finali = f"[Attività svolte: {stringa_attivita_completa}] {note}".strip()
            semaforo_protetto = max(1, min(10, int(round(st.session_state.valore_sem))))
            
            # Payload completo per l'invio dati via Google Moduli
            payload = {
                ENTRY_ID['data']: st.session_state.mattina_data.strftime("%d/%m/%Y"), 
                ENTRY_ID['posizione']: st.session_state.posizione,
                ENTRY_ID['temp']: str(int(round(st.session_state.temp))), 
                ENTRY_ID['umidita']: str(int(st.session_state.umidita)),
                ENTRY_ID['sonno']: st.session_state.sonno, 
                ENTRY_ID['energia']: str(int(st.session_state.energia)),
                ENTRY_ID['passi']: st.session_state.passi, 
                ENTRY_ID['semaforo']: str(semaforo_protetto),
                ENTRY_ID['siesta_form']: "si" if st.session_state.siesta else "no", 
                ENTRY_ID['valutazione']: valutazione,
                ENTRY_ID['dolore']: str(int(dolore)), 
                ENTRY_ID['note']: note_finali,
                ENTRY_ID['crash']: crash_scelta 
            }
            
            if st.session_state.attivita: payload[ENTRY_ID['attivita']] = st.session_state.attivita[0]
            else: payload[ENTRY_ID['attivita']] = "riposo totale"
            
            try:
                r = requests.post(URL_MODULO, data=payload)
                if r.status_code == 200:
                    st.balloons()
                    st.write("✅ Dati registrati nel database con successo! Buona notte 🌟")
                    st.session_state.mattina_salvata = False 
                else: 
                    st.error(f"❌ Errore di trasmissione (Codice HTTP {r.status_code}). Verifica gli ID dei campi.")
            except Exception as e: 
                st.error(f"⚠️ Impossibile raggiungere Google Moduli: {e}")
