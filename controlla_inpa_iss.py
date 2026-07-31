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
    "Referer": "https://www.inpa.gov.it/bandi-e-avvisi/",
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
    "livelliAnzianitaIds": "",
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


def mostra_errore(risposta):
    print()
    print("Risposta restituita dal server InPA:")

    try:
        errore = risposta.json()

        print(
            json.dumps(
                errore,
                indent=2,
                ensure_ascii=False,
            )
        )

    except ValueError:
        contenuto = risposta.text.strip()

        if contenuto:
            print(contenuto[:5000])
        else:
            print("Nessun dettaglio restituito dal server.")


def controlla_inpa_iss():
    print("Ricerca diretta dei concorsi ISS su InPA")
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
        mostra_errore(risposta)
        return

    try:
        dati = risposta.json()

    except ValueError:
        print()
        print("InPA non ha restituito dati JSON validi.")
        print(risposta.text[:5000])
        return

    if not isinstance(dati, dict):
        print()
        print("Formato della risposta non riconosciuto.")
        print(f"Tipo ricevuto: {type(dati).__name__}")
        return

    risultati = dati.get("content", [])
    totale = dati.get("totalElements", 0)
    pagine = dati.get("totalPages", 0)

    print()
    print(f"Risultati totali dichiarati da InPA: {totale}")
    print(f"Pagine disponibili: {pagine}")
    print(
        "Risultati ricevuti nella prima pagina: "
        f"{len(risultati)}"
    )

    if not risultati:
        print()
        print(
            "La richiesta è stata accettata, "
            "ma non ha restituito risultati."
        )
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

        enti = leggi_valore(
            elemento,
            ["entiRiferimento", "enteRiferimento"],
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
        "Nessun file del repository è stato modificato."
    )


if __name__ == "__main__":
    controlla_inpa_iss()
