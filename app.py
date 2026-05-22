import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

st.set_page_config(page_title="Predizione Qualità Giornata", page_icon="📊", layout="centered")

st.title("📊 Il Mio Diario della Giornata")
st.write("Inserisci i dati della giornata per calcolare la predizione basata sul tuo storico.")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1eSnvfouOdaL-sakQgwKCItUEKXN-96ECF93KD96cx-E/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def carica_dati(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error("Errore nel collegamento al Foglio Google. Verifica condivisione e ID.")
        return None

df_storico = carica_dati(URL_FOGLIO)

if df_storico is not None and not df_storico.empty:
    # PULIZIA DATI NUMERICI (Forza i numeri ed elimina i testi errati nelle colonne chiave)
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
        st.warning("⚠️ Attenzione: Assicurati di aver inserito dei NUMERI (es. 21, 22.5) nella colonna 'temperatura meterologica massima' del tuo Foglio Google per far funzionare l'algoritmo!")
    else:
        # Estraiamo le opzioni testuali dal tuo storico
        opzioni_sonno = df_pulito['Qualità del sonno'].unique().tolist()
        opzioni_passi = df_pulito['Passi'].unique().tolist()
        opzioni_attivita = df_pulito['Attività'].unique().tolist()
        
        st.subheader("🗓️ I Parametri di Oggi")
        data_oggi = st.date_input("Data", datetime.date.today())
        
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            # Sostituito il meteo automatico instabile con un controllo manuale numerico preciso
            temp_massima = st.number_input("Temperatura massima giornaliera (°C)", min_value=-10.0, max_value=50.0, value=20.0, step=0.5)
            sonno_scelto = st.selectbox("Qualità del sonno", options=opzioni_sonno)
            energia = st.slider("Energia al risveglio", 1.0, 10.0, 7.0, 0.5)
            
        with col2:
            passi_scelti = st.selectbox("Passi previsti", options=opzioni_passi)
            attivita_scelta = st.selectbox("Attività prevista", options=opzioni_attivita)

        st.write("---")

        # Allenamento del modello di Intelligenza Artificiale
        X_testo = df_pulito[['temperatura meterologica massima', 'Qualità del sonno', 'Energia al risveglio', 'Passi', 'Attività']]
        X_dummy = pd.get_dummies(X_testo, columns=['Qualità del sonno', 'Passi', 'Attività'])
        y = df_pulito['semaforo energetico']
        
        modello = LinearRegression()
        modello.fit(X_dummy, y)

        if st.button("🔮 Calcola Predizione", type="primary"):
            nuovo_giorno = pd.DataFrame([{
                'temperatura meterologica massima': temp_massima,
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
                
            st.info(f"💡 Promemoria per il feedback di stasera: \n`{data_oggi}, {temp_massima}, {sonno_scelto}, {energia}, {passi_scelti}, {attivita_scelta}, [Inserisci Semaforo Reale]`")
else:
    st.warning("Assicurati che il Foglio Google contenga i dati iniziali con i corretti titoli di colonna.")
    
