import streamlit as st
import datetime
import requests
import time
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PRINCIPALE ---
st.set_page_config(page_title="Ogni Giorno - MS Diary", layout="centered", page_icon="🌱")

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

# --- ATTIVITÀ STRUTTURATE PER FUTURO ALGORITMO ---
ATTIVITA_OPZIONI = [
    "ufficio",
    "lavoro da casa",
    "studio",
    "piccole commissioni",
    "visita",
    "fisioterapia",
    "riposo totale",
    "sociale"
]

PESI_ATTIVITA = {
    "ufficio": -0.5,
    "lavoro da casa": -0.2,
    "studio": -0.3,
    "piccole commissioni": -0.4,
    "visita": -0.5,
    "fisioterapia": -0.5,
    "riposo totale": 0.5,
    "sociale": -0.7
}

ATTIVITA_DOMESTICHE = {
    "studio",
    "lavoro da casa",
    "riposo totale"
}

# Nuovi campi tecnici Google Moduli: 1 = attività selezionata, 0 = attività non selezionata
ENTRY_ID_ATTIVITA_BINARIE = {
    "ufficio": "entry.251609888",
    "lavoro da casa": "entry.526360955",
    "studio": "entry.1594094667",
    "piccole commissioni": "entry.349175663",
    "visita": "entry.83072921",
    "fisioterapia": "entry.194539756",
    "riposo totale": "entry.583848141",
    "sociale": "entry.161079508"
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
    'valore_sem': None,
    'ispezione_log': {}
}

for chiave, valore in stato_iniziale.items():
    if chiave not in st.session_state:
        st.session_state[chiave] = valore

# --- FUNZIONE RE-TRY LOGIC ---
def invia_richiesta_con_riconnessione(url, parametri):
    for tentativo in range(3): 
        try:
            risposta = requests.get(url, params=parametri, timeout=5)
            if risposta.status_code == 200:
                return risposta 
            elif risposta.status_code == 429:
                time.sleep(random.uniform(0.5, 2.0))
                continue
            else:
                return risposta
        except requests.exceptions.RequestException:
            time.sleep(random.uniform(0.5, 2.0))
    return None

# --- FUNZIONE INTERNA: CALCOLO DIRETTO DELLE 72 ORE (ACCUMULO) ---
def calcola_accumulo_72ore():
    ispezione = {
        "status": "Inizializzato",
        "righe_rilevate": 0,
        "dettaglio_giorni": []
    }

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl="1m") 
        
        if df is None or len(df) < 3:
            ispezione["status"] = "Storico insufficiente"
            return 0.0, "Storico insufficiente nel database", ispezione
        
        ispezione["righe_rilevate"] = len(df)

        colonna_crash = [c for c in df.columns if 'crash' in c.lower()]
        colonna_match = [c for c in df.columns if 'valutazione' in c.lower() or 'riscontro' in c.lower()]
        
        if not colonna_crash:
            ispezione["status"] = "Colonna crash mancante"
            return 0.0, "Nessun accumulo attivo (Manca colonna Crash)", ispezione
            
        col_c = colonna_crash[0]
        col_m = colonna_match[0] if colonna_match else None
        
        ultimi_3_giorni = df.tail(3).to_dict('records')
        giorni_etichette = ['ieri', 'due_giorni', 'tre_giorni']
        pesi_temporali = {
            'ieri': 1.0,
            'due_giorni': 0.5,
            'tre_giorni': 0.25
        }
        
        accumulo_totale = 0.0
        dettaglio_log = []
        
        for i, etichetta in enumerate(reversed(giorni_etichette)):
            record = ultimi_3_giorni[i]

            val_crash = str(record.get(col_c, '0')).strip().lower()
            val_match = str(record.get(col_m, '')).strip() if col_m else "N/D"
            
            info_giorno = {
                "giorno": etichetta,
                "crash_rilevato": val_crash,
                "riscontro_serale": val_match,
                "peso_temporale": pesi_temporali[etichetta],
                "penalita_applicata": 0.0
            }
            
            if val_crash.startswith('1') or 'si' in val_crash or 'sì' in val_crash:
                impatto = 1.5 * pesi_temporali[etichetta]

                if val_match == "Underestimated":
                    impatto *= 1.5
                    info_giorno["moltiplicatore_protezione"] = "Attivo (x1.5)"
                
                accumulo_totale += impatto
                info_giorno["penalita_applicata"] = round(impatto, 2)
                dettaglio_log.append(f"{etichetta} (-{round(impatto, 2)})")
                
            ispezione["dettaglio_giorni"].append(info_giorno)
            
        stringa_report = " + ".join(dettaglio_log) if dettaglio_log else "Nessun sovraccarico rilevato."
        ispezione["status"] = "Calcolo completato con successo"

        return round(accumulo_totale, 2), stringa_report, ispezione

    except Exception as e:
        ispezione["status"] = f"Errore: {str(e)}"
        return 0.0, "Errore allineamento", ispezione

# --- FUNZIONE METEO ---
@st.cache_data(ttl=60)
def recupera_meteo(data, nome_citta):
    try:
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"
        params_geo = {
            "name": nome_citta.strip(),
            "count": 1,
            "language": "it",
            "format": "json"
        }

        risposta_geo = invia_richiesta_con_riconnessione(url_geo, params_geo)

        if not risposta_geo or risposta_geo.status_code != 200:
            return 20.0, 50, "Errore di rete"

        data_geo = risposta_geo.json()
        lat, lon = 45.43, 10.99

        if "results" in data_geo and len(data_geo["results"]) > 0:
            lat = data_geo["results"][0]["latitude"]
            lon = data_geo["results"][0]["longitude"]
        else:
            return 20.0, 50, "Città non trovata."

        d_str = data.strftime("%Y-%m-%d")

        url_meteo = "https://api.open-meteo.com/v1/forecast"
        params_meteo = {
            "latitude": lat,
            "longitude": lon,
            "start_date": d_str,
            "end_date": d_str,
            "daily": "temperature_2m_max",
            "hourly": "relative_humidity_2m",
            "timezone": "Europe/Rome"
        }

        risposta_meteo = invia_richiesta_con_riconnessione(url_meteo, params_meteo)

        if not risposta_meteo or risposta_meteo.status_code != 200:
            return 20.0, 50, "Errore di rete"

        resp = risposta_meteo.json()

        val_temp = float(resp['daily']['temperature_2m_max'][0])
        umidita_orarie = resp['hourly']['relative_humidity_2m']
        val_umidita = int(sum(umidita_orarie) / len(umidita_orarie))

        return val_temp, val_umidita, None

    except Exception as e:
        return 20.0, 50, str(e)

# --- FUNZIONE: ATTIVITÀ STRUTTURATE NEL PAYLOAD ---
def aggiungi_attivita_strutturate_al_payload(payload, attivita_selezionate):
    """
    Mantiene compatibilità con il vecchio campo 'attivita',
    ma aggiunge anche colonne binarie 1/0 per il futuro algoritmo.
    """

    attivita_selezionate = attivita_selezionate or []
    set_attivita = set(attivita_selezionate)

    # Campo vecchio: salvo ancora una attività principale per compatibilità.
    if attivita_selezionate:
        payload[ENTRY_ID['attivita']] = attivita_selezionate[0]
    else:
        payload[ENTRY_ID['attivita']] = "riposo totale"

    # Campi nuovi: una colonna per attività.
    for nome_attivita, entry_id in ENTRY_ID_ATTIVITA_BINARIE.items():
        if entry_id:
            payload[entry_id] = "1" if nome_attivita in set_attivita else "0"

    return payload

# --- INTERFACCIA UTENTE ---
st.title("🌱 Ogni Giorno")
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

    if errore_rilevato:
        st.warning("⚠️ Centralina meteo sovraccarica. Aggiorna o compila a mano.")

    st.markdown("---") 

    sonno = st.selectbox("💤 Qualità del sonno:", ["discreta", "soddisfacente", "scarsa"])
    passi = st.selectbox("🚶 Passi previsti:", ["fino a 1000", "da 1001 a 3000", "oltre 3000"])
    energia = st.slider("⚡ Energia al risveglio (1-10):", 1, 10, 5)
    siesta = st.checkbox("🛌 Pianifico una siesta strategica/efficace oggi", value=st.session_state.siesta)
    
    attivita = st.multiselect(
        "📅 Attività in programma:",
        ATTIVITA_OPZIONI
    )

    if st.button("🚀 Calcola e Salva Mattina", use_container_width=True):
        accumulo, log_accumulo, debug_data = calcola_accumulo_72ore()
        
        # --- CALCOLO IMPATTO ATTIVITÀ ---
        somma_att = sum([PESI_ATTIVITA[a] for a in attivita])
        
        if len(attivita) > 1:
            label_attivita = "Impatto Sommatoria Attività"
            mult_attivita_extra = (len(attivita) - 1) * -0.3
        else:
            label_attivita = "Impatto Attività Singola" if len(attivita) == 1 else "Nessuna Attività Selezionata"
            mult_attivita_extra = 0.0
            
        # --- LOGICA COMBINATA: CALORE + UMIDITÀ ---
        # Se sono selezionate solo attività domestiche, la penalizzazione climatica esterna viene esclusa.
        solo_attivita_domestiche = (
            len(attivita) > 0 and all(a in ATTIVITA_DOMESTICHE for a in attivita)
        )

        temp_percepita = temp

        if solo_attivita_domestiche:
            p_temp = 0.0
        else:
            if temp >= 27.0 and umidita > 60:
                gradi_extra_umidita = ((umidita - 60) / 10.0) * 0.5
                temp_percepita = temp + gradi_extra_umidita
                
            p_temp = 0.0 if temp_percepita < 28.0 else -0.5 - ((temp_percepita - 28.0) * 0.3)
        
        # --- LOGICA SONNO FISIOLOGICA ---
        peso_sonno = {
            "discreta": 0.0,
            "soddisfacente": 1.5,
            "scarsa": -1.5
        }[sonno]
        
        # --- LOGICA PASSI E SIESTA BILANCIATA ---
        peso_passi = {
            "fino a 1000": 0.2,
            "da 1001 a 3000": -0.2,
            "oltre 3000": -0.5
        }[passi]

        bonus_siesta = 0.4 if siesta else 0.0
        
        score_base = (
            5.0
            + (energia * 0.3)
            + peso_sonno
            + peso_passi
            + somma_att
            + mult_attivita_extra
            + p_temp
            + bonus_siesta
        )

        score_finale = score_base - accumulo
        valore_calcolato = round(max(1.0, min(10.0, score_finale)), 1)
        
        ispezione_giornata = {
            "Valore Energetico al Risveglio": round(energia * 0.3, 2),
            "Impatto Qualità del Sonno": peso_sonno,
            "Impatto Passi Previsti": peso_passi,
            label_attivita: round(somma_att, 2),
            "Accumulo da Sovrapposizione Impegni": round(mult_attivita_extra, 2),
            "Meteo: Temperatura con Afa": f"{round(temp_percepita, 1)} °C",
            "Clima escluso per attività domestica": "sì" if solo_attivita_domestiche else "no",
            "Impatto Clima Esterno": round(p_temp, 2),
            "Bonus Strategico Siesta": bonus_siesta,
            "VALORE DI BASE ODIERNO": round(score_base, 2),
            "IMPATTO DELL'ACCUMULO (ULTIME 72H)": -accumulo,
            "VALORE PONDERATO FINALE": valore_calcolato,
            "Storico Database Usato": debug_data
        }
        
        st.session_state.update({
            'mattina_salvata': True,
            'mattina_data': data_sel,
            'posizione': posizione_input, 
            'temp': temp,
            'umidita': umidita,
            'sonno': sonno,
            'passi': passi, 
            'energia': energia,
            'attivita': attivita,
            'siesta': siesta, 
            'valore_sem': valore_calcolato,
            'ispezione_log': ispezione_giornata
        })
        
        st.markdown("---") 

        # Il calcolo dell'accumulo resta attivo, ma il banner "Scudo Carico Attivo" non viene più mostrato.
        if accumulo <= 0:
            st.caption(f"📊 Controllo Storico: {log_accumulo}")
            
        if valore_calcolato <= 4.5:
            st.error(f"🔴 BOLLINO ROSSO: {valore_calcolato} Dai priorità al riposo 🐢")
        elif valore_calcolato <= 7.0:
            st.warning(f"🟡 BOLLINO GIALLO: {valore_calcolato} Giornata regolare, procedi con calma 🐘")
        else:
            st.success(f"🟢 BOLLINO VERDE: {valore_calcolato} Ottima carica! 🦋")

# ==========================================
# TAB SERA 
# ==========================================
with tab_sera:
    if not st.session_state.mattina_salvata:
        st.warning("⚠️ Compila e salva prima i dati del mattino nella scheda precedente!")
    else:
        st.subheader("Com'è andata la giornata?")
        st.markdown(f"Punteggio stimato stamattina: **{st.session_state.valore_sem}**")
        
        crash_scelta = st.radio(
            "💥 C'è stato un crash/sovraccarico oggi?", 
            ["0 - no", "1 - si"],
            index=0,
            horizontal=True
        )
        
        valutazione = st.selectbox(
            "Il punteggio del mattino era corretto? (Riscontro):",
            ["Match", "Overestimated", "Underestimated"]
        )

        dolore = st.slider("Livello dolore avvertito (1-10):", 1, 10, 1)
        note = st.text_area("Note o riflessioni serali:", placeholder="Scrivi qui le tue annotazioni...")
        
        if st.button("💾 REGISTRA IL MIO DIARIO", use_container_width=True):
            stringa_attivita_completa = ", ".join(st.session_state.attivita) if st.session_state.attivita else "Nessuna"
            note_finali = f"[Attività svolte: {stringa_attivita_completa}] {note}".strip()
            semaforo_protetto = max(1, min(10, int(round(st.session_state.valore_sem))))
            
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

            payload = aggiungi_attivita_strutturate_al_payload(
                payload,
                st.session_state.attivita
            )
            
            try:
                r = requests.post(URL_MODULO, data=payload)

                if r.status_code == 200:
                    st.balloons()
                    st.success("Dati registrati con successo! Buona notte")
                    st.session_state.mattina_salvata = False 
                else: 
                    st.error(f"❌ Errore di trasmissione (Codice HTTP {r.status_code}).")

            except Exception as e: 
                st.error(f"⚠️ Errore connessione modulo: {e}")

# ==========================================
# BARRA LATERALE - ISPEZIONE ALLINEATA ED ESSENZIALE
# ==========================================
with st.sidebar:
    st.header("🔬 Ispezione Algoritmo")

    if not st.session_state.ispezione_log:
        st.info("Esegui un calcolo nel Tab Mattina per attivare la telemetria.")
    else:
        st.subheader("Analisi della giornata")
        
        # Mostra prima le voci di calcolo intermedie, escludendo i valori di sintesi
        for voce, valore in st.session_state.ispezione_log.items():
            if voce not in [
                "Storico Database Usato",
                "VALORE DI BASE ODIERNO",
                "IMPATTO DELL'ACCUMULO (ULTIME 72H)",
                "VALORE PONDERATO FINALMENTE",
                "VALORE PONDERATO FINALE",
                "Punto di Partenza Fisso"
            ]:
                st.text(f"• {voce}: {valore}")
        
        st.markdown("---")
        
        # Blocco valori di sintesi formattati in modo identico e pulito senza icone
        base_val = st.session_state.ispezione_log.get("VALORE DI BASE ODIERNO", 0.0)
        acc_val = st.session_state.ispezione_log.get("IMPATTO DELL'ACCUMULO (ULTIME 72H)", 0.0)
        fin_val = st.session_state.ispezione_log.get("VALORE PONDERATO FINALE", 0.0)
        
        st.text(f"VALORE DI BASE ODIERNO: {base_val}")
        st.text(f"IMPATTO DELL'ACCUMULO (ULTIME 72H): {acc_val}")
        st.text(f"VALORE PONDERATO FINALE: {fin_val}")
        
        st.markdown("---")
        st.subheader("Lettura Storico 72h")

        db_debug = st.session_state.ispezione_log["Storico Database Usato"]

        st.caption(f"Stato: {db_debug['status']}")
        st.caption(f"Righe totali database: {db_debug['righe_rilevate'] if 'righe_rilevate' in db_debug else 0}")
        
        if "dettaglio_giorni" in db_debug and db_debug["dettaglio_giorni"]:
            for giorno in db_debug["dettaglio_giorni"]:
                with st.expander(f"📅 Analisi {giorno['giorno'].upper()}"):
                    st.write(f"**Crash registrato:** `{giorno['crash_rilevato']}`")
                    st.write(f"**Riscontro serale:** `{giorno['riscontro_serale']}`")
                    st.write(f"**Peso temporale:** {giorno['peso_temporale'] * 100}%")

                    if "moltiplicatore_protezione" in giorno:
                        st.warning("⚠️ Scudo attivo (Sotto-stimato x1.5)")

                    st.write(f"**Penalità calcolata:** -{giorno['penalita_applicata']}")
