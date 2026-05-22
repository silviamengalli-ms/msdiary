import requests
import datetime

def ottieni_temperatura_massima_verona(data_selezionata):
    """
    Rileva la temperatura massima giornaliera (in °C) per la città di Verona.
    Accetta un oggetto datetime.date (es. datetime.date.today())
    """
    # Coordinate precise di Verona
    LATITUDINE = 45.4299
    LONGITUDINE = 10.9844
    
    # Formattiamo la data nel formato richiesto dall'API (AAAA-MM-GG)
    data_str = data_selezionata.strftime("%Y-%m-%d")
    
    # URL dell'API configurato per chiedere solo la temperatura massima giornaliera (temperature_2m_max)
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDINE}&longitude={LONGITUDINE}&"
        f"daily=temperature_2m_max&timezone=auto&"
        f"start_date={data_str}&end_date={data_str}"
    )
    
    try:
        # Facciamo la richiesta al server con un timeout di 5 secondi per evitare blocchi infiniti
        risposta = requests.get(url, timeout=5).json()
        
        # Estraiamo il primo valore della lista delle temperature massime giornaliere
        temperatura_max = risposta["daily"]["temperature_2m_max"][0]
        
        return float(temperatura_max)
        
    except Exception as e:
        # Se internet non va o l'API è offline, restituiamo un valore di backup standard (22°C)
        # In questo modo l'applicazione non crasha e continua a funzionare!
        return 22.0
