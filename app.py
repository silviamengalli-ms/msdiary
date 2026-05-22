import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
import requests

st.set_page_config(page_title="Predizione Qualità Giornata", page_icon="📊", layout="centered")

st.title("📊 Il Mio Diario della Giornata")
st.write("Compila i menu a discesa per calcolare la predizione basata sul tuo storico.")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

# FUNZIONE METEO AUTOMATICA
def ottieni_temperatura_citta(citta, data_selezionata):
    try:
        url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={citta}&count=1&language=it&format=json"
        res_geo = requests.get(url_geo).json()
        if not res_geo.get("results"):
            return None
        lat = res_geo["results"][0]["latitude"]
        lon = res_geo["results"][0]["longitude"]
        
        data_str = data_selezionata.strftime("%Y-%m-%d")
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max&timezone=auto&start_date={data_str}&end_date={data_str}"
        res_meteo = requests.get(url_meteo).json()
        return res_meteo["daily"]["temperature_2m_max"][0]
    except:
        return None

@st.cache_data(ttl=10)
def carica_dati(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error("Errore nel collegamento al Foglio Google. Verifica condivisione e ID.")
        return None

df_storico = carica_dati(URL_FOGLIO)

if df_storico is not None and not df_storico.empty:
    # PULIZIA DI SICUREZZA: Trasforma le virgole in punti e forza in numero
    if 'Energia al risveglio' in df_storico.columns:
        df_storico['Energia al risveglio'] = df_storico['Energia al risveglio'].astype(str).str.replace(',', '.')
        df_storico['Energia al risveglio'] = pd.to_numeric(df_storico['Energia al risveglio'], errors='coerce')
    
    if 'semaforo energetico' in df_storico.columns:
        df_storico['semaforo energetico'] = df_storico['semaforo energetico'].astype(str).str.replace(',', '.')
        df_storico['semaforo energetico'] = pd.to_numeric(df_storico['semaforo energetico'], errors='coerce')

    df_pulito = df_storico.dropna(subset=[
        'temperatura meterologica massima', 
        'Qualità del sonno', 
        'Energia al risveglio', 
        'Passi', 
        'Attività', 
        'semaforo energetico'
    ])
    
    if df_pulito.empty:
        st.warning("⚠️ Attenzione: Dopo aver pulito i dati, nessuna riga è risultata valida. Controlla che le colonne 'Energia al risveglio' e 'semaforo energetico' contengano solo numeri nel tuo Foglio Google.")
    else:
        opzioni_meteo = df_pulito['temperatura meterologica massima'].unique().tolist()
        opzioni_sonno = df_pulito['Qualità del sonno'].unique().tolist()
        opzioni_passi = df_pulito['Passi'].unique().tolist()
        opzioni_attivita = df_pulito['Attività'].unique().tolist()
        
        st.subheader("🗓️ Compila i parametri di Oggi")
        data_oggi = st.date_input("Data", datetime.date.today())
        
        temp_rilevata = ottieni_temperatura_citta("Verona", data_oggi)
        if temp_rilevata:
            st.info(f"🌤️ Temperatura massima stimata a Verona oggi: **{temp_rilevata}°C**. Usa questo dato come riferimento per i menu sotto.")

        st.write("---")

        col1, col2 = st.columns(2)
        with col1:
            meteo_scelto = st.selectbox("Temperatura meteo massima", options=opzioni_meteo)
            sonno_scelto = st.selectbox("Qualità del sonno", options=opzioni_sonno)
            energia = st.slider("Energia al risveglio (Valore Numerico)", 1.0, 10.0, 7.0, 0.5)
            
        with col2:
            passi_scelti = st.selectbox("Passi previsti", options=opzioni_passi)
            attivita_scelta = st.selectbox("Attività prevista", options=opzioni_attivita)

        st.write("---")

        X_testo = df_pulito[['temperatura meterologica massima', 'Qualità del sonno', 'Energia al risveglio', 'Passi', 'Attività']]
        X_dummy = pd.get_dummies(X_testo, columns=['temperatura meterologica massima', 'Qualità del sonno', 'Passi', 'Attività'])
        y = df_pulito['semaforo energetico']
        
        modello = LinearRegression()
        modello.fit(X_dummy, y)

        if st.button("🔮 Calcola Predizione", type="primary"):
            nuovo_giorno = pd.DataFrame([{
                'temperatura meterologica massima': meteo_scelto,
                'Qualità del sonno': sonno_scelto,
                'Energia al risveglio': energia,
                'Passi': passi_scelti,
                'Attività': attivita_scelta
            }])
            
            nuovo_giorno_dummy = pd.get_dummies(nuovo_giorno, columns=['temperatura meterologica massima', 'Qualità del sonno', 'Passi', 'Attività'])
            nuovo_giorno_dummy = nuovo_giorno_dummy.reindex(columns=X_dummy.columns, fill_value=0)
            
            predizione = modello.predict(nuovo_giorno_dummy)[0]
            predizione = max(1.0, min(10.0, predizione))
            
            st.success(f"### 🎯 Predizione Semaforo Energetico")
            st.metric(label="Valore ipotetico stimato per oggi", value=f"{predizione:.1f} / 10")
            
            if predizione >= 7.5:
                st.balloons()
                st.write("✨ Giornata promettente! I parametri indicano un'ottima efficacia energetica.")
            elif predizione >= 5.5:
                st.write("👍 Giornata equilibrata. Carichi in linea con le tue giornate standard.")
            else:
                st.write("⚠️ Attenzione ai carichi. Questa combinazione storicamente ti richiede molta energia.")
                
            st.info(f"💡 Promemoria per il feedback di stasera: \n`{data_oggi}, {meteo_scelto}, {sonno_scelto}, {energia}, {passi_scelti}, {attivita_scelta}, [Inserisci Semaforo Reale]`")
else:
    st.warning("Assicurati che il Foglio Google contenga i dati iniziali con i testi corretti per popolare i menu a discesa.")
