# ==========================================
# TAB SERA (Consuntivo e Invio) - VERSIONE CORRETTA E RIALLINEATA
# ==========================================
with tab_sera:
    if not st.session_state.mattina_salvata:
        st.warning("⚠️ Compila e salva prima i dati del mattino nella scheda precedente!")
    else:
        st.subheader("Com'è andata la giornata?")
        st.markdown(f"Stamattina il sistema aveva previsto un semaforo di: **{st.session_state.valore_sem}**")
        
        valutazione = st.selectbox("Il punteggio del mattino era corretto? (Riscontro):", ["Match", "Overestimated", "Underestimated"])
        dolore = st.slider("Livello dolore avvertito (1-10):", 1, 10, 1)
        note = st.text_area("Note o riflessioni serali:", placeholder="Scrivi qui le tue annotazioni... (#sintomi, #clima, #umore)")
        
        if st.button("💾 REGISTRA IL MIO DIARIO", use_container_width=True):
            
            stringa_attivita_completa = ", ".join(st.session_state.attivita) if st.session_state.attivita else "Nessuna"
            note_finali = f"[Attività svolte: {stringa_attivita_completa}] {note}".strip()
            
            payload = {
                ENTRY_ID['data']: st.session_state.mattina_data.strftime("%d/%m/%Y"),
                ENTRY_ID['posizione']: st.session_state.posizione,
                ENTRY_ID['temp']: str(int(round(st.session_state.temp))),
                ENTRY_ID['umidita']: str(int(st.session_state.umidita)),
                ENTRY_ID['sonno']: st.session_state.sonno,
                ENTRY_ID['energia']: str(int(st.session_state.energia)),
                ENTRY_ID['passi']: st.session_state.passi,
                ENTRY_ID['semaforo']: str(int(round(st.session_state.valore_sem))),
                ENTRY_ID['valutazione']: valutazione,
                ENTRY_ID['dolore']: str(int(dolore)),
                ENTRY_ID['note']: note_finali
            }
            
            if st.session_state.attivita:
                payload[ENTRY_ID['attivita']] = st.session_state.attivita[0]
            else:
                payload[ENTRY_ID['attivita']] = "riposo totale"
            
            try:
                r = requests.post(URL_MODULO, data=payload)
                if r.status_code == 200:
                    st.balloons()
                    st.write("✅ Dati registrati con successo nel tuo diario! Buona notte e sogni d'oro! 🌟")
                    st.session_state.mattina_salvata = False 
                else:
                    st.error(f"❌ Errore di salvataggio (Codice HTTP {r.status_code}). Verifica la configurazione dei campi.")
            except Exception as e:
                st.error(f"⚠️ Impossibile raggiungere Google Moduli: {e}")
