import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
import requests

st.set_page_config(page_title="Predizione Qualità Giornata", page_icon="📊", layout="centered")

st.title("📊 Il Mio Diario della Giornata")
st.write("L'app rileva il meteo automaticamente e calcola la predizione basata sul tuo storico.")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# FUNZIONE METEO AGGIORNATA E PIÙ ROBUSTA
def ottieni_temperatura_citta(citta, data_selezionata):
    try:
        # 1. Trova le coordinate di Verona
        url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={citta}&count=1&language=it&format=json"
        res_geo = requests.get(url_geo, timeout=5).json()
        if not res_geo.get("results"):
            return 22.0 # Backup se il geocoding fallisce
        lat = res_geo["results"][0]["latitude"]
        lon = res_geo["results"][0]["longitude"]
        
        # 2. Se è oggi, usiamo il meteo attuale/previsione semplice, altrimenti cerchiamo la data specifica
        if data_selezionata == datetime.date.today():
            url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max&timezone=auto"
        else:
            data_str = data_selezionata.strftime("%Y-%m-%d")
            url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max&timezone=auto&start_date={data_str}&end_date={data_str}"
            
        res_meteo = requests.get(url_meteo, timeout=5).json()
        return float(res_meteo["daily"]["temperature_2m_max"][0])
    except:
        return 22.0 # Temperatura di backup standard se l'API non risponde

@st.cache_data(ttl=5)
def carica_dati(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error("Errore nel collegamento al Foglio Google. Verifica condivisione e ID.")
        return None

df_storico = carica_dati(URL_FOGLIO)

if df_storico is not None and not df_storico.empty:
    # PULIZIA DATI NUMERICI
    for col in ['temperatura meterologica massima', 'Energia al risveglio', 'semaforo energetico']:
        if col in df_storico.columns:
            df_storico[col] = df_storico[col].astype(str).str.replace(',', '.')
            df_storico[col] = pd.to_numeric(df_storico[col], errors='coerce')

    df_pulito = df_storico.dropna(subset=[
        'temperatura meterologica massima', 
        'Qualità del sonno', 
        'Energia al risveglio', 
        'Passi', 
        'Attività', 
        'semaforo energetico'
    ])
    
    if df_pulito.empty:
        st.warning("⚠️ Per attivare il meteo automatico, assicurati di aver inserito dei NUMERI (es. 20, 22.5) nella colonna 'temperatura meterologica massima' del tuo Foglio Google!")
    else:
        opzioni_sonno = df_pulito['Qualità del sonno'].unique().tolist()
        opzioni_passi = df_pulito['Passi'].unique().tolist()
        opzioni_attivita = df_pulito['Attività'].unique().tolist()
        
        st.subheader("🗓️ I Parametri di Oggi")
        data_oggi = st.date_input("Data", datetime.date.today())
        
        # Rilevamento automatico della temperatura
        temp_rilevata = ottieni_temperatura_citta("Verona", data_oggi)
        
        st.success(f"🌤️ **Meteo stimato a Verona:** {temp_rilevata}°C")
        
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            sonno_scelto = st.selectbox("Qualità del sonno", options=opzioni_sonno)
            energia = st.slider("Energia al risveglio", 1.0, 10.0, 7.0, 0.5)
            
        with col2:
            passi_scelti = st.selectbox("Passi previsti", options=opzioni_passi)
            attivita_scelta = st.selectbox("Attività prevista", options=opzioni_attivita)

        st.write("---")

        # Allenamento modello con temperatura numerica
        X_testo = df_pulito[['temperatura meterologica massima', 'Qualità del sonno', 'Energia al risveglio', 'Passi', 'Attività']]
        X_dummy = pd.get_dummies(X_testo, columns=['Qualità del sonno', 'Passi', 'Attività'])
        y = df_pulito['semaforo energetico']
        
        modello = LinearRegression()
        modello.fit(X_dummy, y)

        if st.button("🔮 Calcola Predizione", type="primary"):
            nuovo_giorno = pd.DataFrame([{
                'temperatura meterologica massima': temp_rilevata,
                'Qualità del sonno': sonno_scelto,
                'Energia al risveglio': energia,
                'Passi': passi_scelti,
                'Attività': attivita_scelta
            }])
            
            nuovo_giorno_dummy = pd.get_dummies(nuovo_giorno, columns=['Qualità del sonno', 'Passi', 'Attività'])
            nuovo_giorno_dummy = nuovo_giorno_dummy.reindex(columns=X_dummy.columns, fill_value=0)
            
            predizione = modello.predict(nuovo_giorno_dummy)[0]
            predizione = max(1.0, min(10.0, predizione))
            
            st.success(f"### 🎯 Predizione Semaforo Energetico")
            st.metric(label="Valore ipotetico stimato per oggi", value=f"{predizione:.1f} / 10")
            
            if predizione >= 7.5:
                st.balloons()
                st.write("✨ Giornata promettente! Ottima efficacia energetica stimata.")
            elif predizione >= 5.5:
                st.write("👍 Giornata equilibrata in linea con i tuoi standard.")
            else:
                st.write("⚠️ Attenzione ai carichi. Questa combinazione ti richiederà molta energia.")
                
            st.info(f"💡 Promemoria per il feedback di stasera: \n`{data_oggi}, {temp_rilevata}, {sonno_scelto}, {energia}, {passi_scelti}, {attivita_scelta}, [Inserisci Semaforo Reale]`")
else:
    st.warning("Assicurati che il Foglio Google contenga i dati iniziali con i corretti titoli di colonna.")
