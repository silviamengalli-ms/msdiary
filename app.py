# --- INVIO DATI (VERSIONE BLINDATA) ---
if st.button("💾 Registra Giornata Definitiva", type="primary"):
    # Componiamo la nota senza caratteri speciali dubbi
    note_complete = f"{feedback} {note_input}" if note_input.strip() else feedback
    
    # Prepariamo il payload
    payload = {
        ENTRY_ID['data']: data_selezionata.strftime("%d/%m/%Y"), # Formato testuale DD/MM/YYYY
        ENTRY_ID['posizione']: posizione,
        ENTRY_ID['temp']: str(int(temp)),
        ENTRY_ID['sonno']: sonno,
        ENTRY_ID['energia']: str(energia),
        ENTRY_ID['dolore']: str(dolore), 
        ENTRY_ID['semaforo']: str(int(round(valore_calcolato))),
        ENTRY_ID['passi']: passi,
        ENTRY_ID['note']: note_complete
    }
    
    # Gestione attività multiple
    payload_lista = [(k, v) for k, v in payload.items()]
    for a in attivita:
        payload_lista.append((ENTRY_ID['attivita'], a))
    
    try:
        # Usiamo headers per simulare un browser e inviare il form
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(URL_MODULO, data=payload_lista, headers=headers)
        
        if response.status_code == 200:
            st.success("🎉 Registrazione riuscita!")
        else:
            st.error(f"Errore {response.status_code}. Il modulo non ha accettato i dati.")
            st.write("Dati inviati:", payload_lista)
    except Exception as e:
        st.error(f"Errore critico: {e}")
