import re

import requests


SCRIPT_DA_ANALIZZARE = [
    (
        "https://www.inpa.gov.it/wp-content/plugins/"
        "dro-dashboard/modules/dro-cerca-bandi/assets/js/"
        "dro-cerca-bandi.js?ver=6.8.3"
    ),
    (
        "https://www.inpa.gov.it/wp-content/plugins/"
        "dro-dashboard/assets/js/"
        "dro-bandi-functions.js?ver=6.8.3"
    ),
]

PAROLE_DA_CERCARE = [
    "admin-ajax",
    "wp-json",
    "ajax",
    "api",
    "endpoint",
    "fetch",
    "action",
    "bandi",
    "concorsi",
]

INTESTAZIONI = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
    )
}


def scarica_script(url):
    try:
        risposta = requests.get(
            url,
            headers=INTESTAZIONI,
            timeout=30,
        )
        risposta.raise_for_status()
        return risposta.text

    except requests.RequestException as errore:
        print(f"Errore nel download di: {url}")
        print(f"Dettaglio: {errore}")
        return None


def trova_indizi(testo):
    risultati = []
    gia_visti = set()

    testo_minuscolo = testo.lower()

    for parola in PAROLE_DA_CERCARE:
        posizione_iniziale = 0

        while True:
            posizione = testo_minuscolo.find(
                parola,
                posizione_iniziale,
            )

            if posizione == -1:
                break

            inizio = max(0, posizione - 180)
            fine = min(len(testo), posizione + 300)

            frammento = testo[inizio:fine]
            frammento = " ".join(frammento.split())

            if frammento not in gia_visti:
                gia_visti.add(frammento)
                risultati.append(
                    {
                        "parola": parola,
                        "frammento": frammento,
                    }
                )

            posizione_iniziale = posizione + len(parola)

    return risultati


def trova_url(testo):
    url_trovati = re.findall(
        r"https?://[^\s\"'<>]+",
        testo,
    )

    risultati = []

    for url in url_trovati:
        url_minuscolo = url.lower()

        if any(
            parola in url_minuscolo
            for parola in [
                "api",
                "ajax",
                "wp-json",
                "band",
                "concors",
            ]
        ):
            if url not in risultati:
                risultati.append(url)

    return risultati


def controlla_script_inpa():
    print("Analisi degli script di ricerca InPA")
    print()

    for numero, url in enumerate(
        SCRIPT_DA_ANALIZZARE,
        start=1,
    ):
        print(f"Script {numero}")
        print(url)

        testo = scarica_script(url)

        if testo is None:
            print()
            continue

        print(f"Dimensione: {len(testo)} caratteri")

        url_interessanti = trova_url(testo)

        print(
            "URL potenzialmente interessanti: "
            f"{len(url_interessanti)}"
        )

        for indirizzo in url_interessanti:
            print(f"- {indirizzo}")

        indizi = trova_indizi(testo)

        print(
            "Frammenti potenzialmente interessanti: "
            f"{len(indizi)}"
        )

        for indice, risultato in enumerate(
            indizi[:20],
            start=1,
        ):
            print()
            print(
                f"Indizio {indice} "
                f"[{risultato['parola']}]"
            )
            print(risultato["frammento"])

        if len(indizi) > 20:
            print()
            print(
                "Altri frammenti non mostrati: "
                f"{len(indizi) - 20}"
            )

        print()
        print("-" * 60)
        print()

    print("Analisi completata.")


if __name__ == "__main__":
    controlla_script_inpa()
