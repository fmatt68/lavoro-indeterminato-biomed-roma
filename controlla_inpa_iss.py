import json
import time

import requests


API_URL = (
    "https://portale.inpa.gov.it/"
    "concorsi-smart/api/concorso-public-area/"
    "search-better?page=0&size=5"
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

TEST_DA_ESEGUIRE = [
    {
        "nome": "Corpo JSON vuoto",
        "dati": {},
    },
    {
        "nome": "Solo ricerca testuale ISS",
        "dati": {
            "text": "Istituto Superiore di Sanità",
        },
    },
    {
        "nome": "Solo filtro per ente ISS",
        "dati": {
            "enteRiferimentoName": (
                "Istituto Superiore di Sanità"
            ),
        },
    },
    {
        "nome": "Campi non usati impostati a null",
        "dati": {
            "text": "",
            "categoriaId": None,
            "regioneId": None,
            "status": None,
            "settoreId": None,
            "provinciaCodice": None,
            "dateFrom": None,
            "dateTo": None,
            "livelliAnzianitaIds": None,
            "tipoImpiegoId": None,
            "salaryMin": None,
            "salaryMax": None,
            "enteRiferimentoName": (
                "Istituto Superiore di Sanità"
            ),
        },
    },
    {
        "nome": "Struttura completa con liste",
        "dati": {
            "text": "",
            "categoriaId": [],
            "regioneId": [],
            "status": [],
            "settoreId": [],
            "provinciaCodice": "",
            "dateFrom": None,
            "dateTo": None,
            "livelliAnzianitaIds": [],
            "tipoImpiegoId": [],
            "salaryMin": None,
            "salaryMax": None,
            "enteRiferimentoName": (
                "Istituto Superiore di Sanità"
            ),
        },
    },
]


def mostra_risposta(risposta):
    print(f"Stato HTTP: {risposta.status_code}")

    contenuto = risposta.text.strip()

    if risposta.ok:
        try:
            dati = risposta.json()
        except ValueError:
            print("Risposta ricevuta, ma non in formato JSON.")
            print(contenuto[:1000])
            return False

        if isinstance(dati, dict):
            totale = dati.get("totalElements")
            risultati = dati.get("content", [])

            print(f"Risultati totali: {totale}")
            print(
                "Risultati nella prima pagina: "
                f"{len(risultati)}"
            )

            if risultati:
                primo = risultati[0]

                print()
                print("Primo risultato ricevuto:")
                print(
                    "Titolo: "
                    f"{primo.get('titolo', 'Non disponibile')}"
                )
                print(
                    "Enti: "
                    f"{primo.get('entiRiferimento', 'Non disponibile')}"
                )

            return True

        print(
            "Risposta JSON ricevuta, "
            "ma con struttura inattesa."
        )
        print(
            json.dumps(
                dati,
                indent=2,
                ensure_ascii=False,
            )[:1000]
        )
        return True

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
        if contenuto:
            print(contenuto[:1000])
        else:
            print("Nessun dettaglio restituito dal server.")

    return False


def esegui_test(nome, dati):
    print()
    print("=" * 60)
    print(f"TEST: {nome}")
    print("=" * 60)

    print("Corpo JSON:")
    print(
        json.dumps(
            dati,
            indent=2,
            ensure_ascii=False,
        )
    )
    print()

    try:
        risposta = requests.post(
            API_URL,
            headers=INTESTAZIONI,
            json=dati,
            timeout=30,
        )
    except requests.RequestException as errore:
        print("Errore di collegamento.")
        print(f"Dettaglio: {errore}")
        return False

    return mostra_risposta(risposta)


def diagnostica_api_inpa():
    print("Diagnostica dei filtri API InPA")
    print()
    print(
        "Questo test non modifica alcun file "
        "del repository."
    )

    test_riusciti = []

    for test in TEST_DA_ESEGUIRE:
        riuscito = esegui_test(
            test["nome"],
            test["dati"],
        )

        if riuscito:
            test_riusciti.append(test["nome"])

        time.sleep(1)

    print()
    print("=" * 60)
    print("RIEPILOGO")
    print("=" * 60)

    if test_riusciti:
        print("Test accettati dall'API:")

        for nome in test_riusciti:
            print(f"- {nome}")
    else:
        print(
            "Nessuno dei corpi JSON provati "
            "è stato accettato dall'API."
        )

    print()
    print(
        "Diagnostica completata. "
        "Nessun CSV è stato modificato."
    )


if __name__ == "__main__":
    diagnostica_api_inpa()
