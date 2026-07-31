import requests


API_URL = (
    "https://portale.inpa.gov.it/"
    "concorsi-smart/api/concorso-public-area/"
    "search-better?page=0&size=20"
)

INTESTAZIONI = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.inpa.gov.it",
    "Referer": "https://www.inpa.gov.it/",
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
    ),
}

FILTRO_ISS = {
    "text": "",
    "categoriaId": "",
    "regioneId": "",
    "status": "",
    "settoreId": "",
    "provinciaCodice": "",
    "dateFrom": "",
    "dateTo": "",
    "livelliAnzianitaIds": [],
    "tipoImpiegoId": "",
    "salaryMin": "",
    "salaryMax": "",
    "enteRiferimentoName": "Istituto Superiore di Sanità",
}


def leggi_valore(elemento, possibili_chiavi):
    for chiave in possibili_chiavi:
        valore = elemento.get(chiave)

        if valore not in [None, "", []]:
            return valore

    return "Non disponibile"


def controlla_inpa_iss():
    print("Ricerca diretta dei concorsi ISS su InPA")
    print()

    try:
        risposta = requests.post(
            API_URL,
            headers=INTESTAZIONI,
            json=FILTRO_ISS,
            timeout=30,
        )

        print(f"Stato HTTP: {risposta.status_code}")
        risposta.raise_for_status()

    except requests.RequestException as errore:
        print("Errore durante la richiesta all'API InPA.")
        print(f"Dettaglio: {errore}")
        return

    try:
        dati = risposta.json()

    except ValueError:
        print("InPA non ha restituito una risposta JSON valida.")
        print()
        print("Primi 1000 caratteri della risposta:")
        print(risposta.text[:1000])
        return

    if not isinstance(dati, dict):
        print("Formato della risposta InPA non riconosciuto.")
        print(type(dati).__name__)
        return

    numero_totale = dati.get("totalElements", 0)
    numero_pagine = dati.get("totalPages", 0)
    risultati = dati.get("content", [])

    print(f"Risultati totali dichiarati da InPA: {numero_totale}")
    print(f"Pagine disponibili: {numero_pagine}")
    print(f"Risultati ricevuti in questa pagina: {len(risultati)}")

    if not risultati:
        print()
        print("Nessun concorso ISS restituito dalla ricerca.")
        return

    for numero, elemento in enumerate(risultati, start=1):
        identificativo = leggi_valore(
            elemento,
            ["id", "concorsoId", "concorso_id"],
        )

        titolo = leggi_valore(
            elemento,
            ["titolo", "title", "descrizione"],
        )

        stato = leggi_valore(
            elemento,
            ["status", "stato", "descrizioneStato"],
        )

        pubblicazione = leggi_valore(
            elemento,
            ["dataPubblicazione", "publicationDate"],
        )

        scadenza = leggi_valore(
            elemento,
            ["dataScadenza", "expirationDate"],
        )

        enti = leggi_valore(
            elemento,
            ["entiRiferimento", "enteRiferimento"],
        )

        print()
        print(f"Risultato {numero}")
        print(f"ID: {identificativo}")
        print(f"Titolo: {titolo}")
        print(f"Ente: {enti}")
        print(f"Stato: {stato}")
        print(f"Pubblicazione: {pubblicazione}")
        print(f"Scadenza: {scadenza}")

        if identificativo != "Non disponibile":
            print(
                "Pagina InPA: "
                "https://www.inpa.gov.it/bandi-e-avvisi/"
                "dettaglio-bando-avviso/"
                f"?concorso_id={identificativo}"
            )

    print()
    print(
        "Test completato. Nessun file CSV è stato modificato."
    )


if __name__ == "__main__":
    controlla_inpa_iss()
