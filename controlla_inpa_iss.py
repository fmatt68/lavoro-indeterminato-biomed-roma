import json

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


def mostra_risposta_errore(risposta):
    print()
    print("Risposta restituita dal server InPA:")
    print()

    contenuto = risposta.text.strip()

    if not contenuto:
        print("Il server non ha restituito alcun testo.")
        return

    try:
        dati_errore = risposta.json()

        print(
            json.dumps(
                dati_errore,
                indent=2,
                ensure_ascii=False,
            )
        )

    except ValueError:
        print(contenuto[:5000])


def controlla_inpa_iss():
    print("Ricerca diretta dei concorsi ISS su InPA")
    print()

    print("Indirizzo API:")
    print(API_URL)
    print()

    print("Filtro inviato:")
    print(
        json.dumps(
            FILTRO_ISS,
            indent=2,
            ensure_ascii=False,
        )
    )
    print()

    try:
        risposta = requests.post(
            API_URL,
            headers=INTESTAZIONI,
            json=FILTRO_ISS,
            timeout=30,
        )

    except requests.RequestException as errore:
        print("Errore durante il collegamento all'API InPA.")
        print(f"Dettaglio: {errore}")
        return

    print(f"Stato HTTP: {risposta.status_code}")
    print(
        "Tipo di contenuto: "
        f"{risposta.headers.get('Content-Type', 'non indicato')}"
    )

    if not risposta.ok:
        mostra_risposta_errore(risposta)
        return

    try:
        dati = risposta.json()

    except ValueError:
        print()
        print("InPA non ha restituito una risposta JSON valida.")
        print()
        print("Primi 5000 caratteri della risposta:")
        print(risposta.text[:5000])
        return

    if not isinstance(dati, dict):
        print()
        print("Formato della risposta InPA non riconosciuto.")
        print(f"Tipo ricevuto: {type(dati).__name__}")
        print()
        print(
            json.dumps(
                dati,
                indent=2,
                ensure_ascii=False,
            )[:5000]
        )
        return

    numero_totale = dati.get("totalElements", 0)
    numero_pagine = dati.get("totalPages", 0)
    risultati = dati.get("content", [])

    print()
    print(
        "Risultati totali dichiarati da InPA: "
        f"{numero_totale}"
    )
    print(f"Pagine disponibili: {numero_pagine}")
    print(
        "Risultati ricevuti in questa pagina: "
        f"{len(risultati)}"
    )

    if not risultati:
        print()
        print("Nessun concorso ISS restituito dalla ricerca.")
        return

    for numero, elemento in enumerate(
        risultati,
        start=1,
    ):
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
        "Test completato. "
        "Nessun file CSV è stato modificato."
    )


if __name__ == "__main__":
    controlla_inpa_iss()
