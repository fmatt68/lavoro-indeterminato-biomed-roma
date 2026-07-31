import re

import requests


URL_SCRIPT = (
    "https://www.inpa.gov.it/wp-content/plugins/"
    "dro-dashboard/modules/dro-cerca-bandi/assets/js/"
    "dro-cerca-bandi.js?ver=6.8.3"
)

INTESTAZIONI = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
    )
}

TERMINI = [
    "getBandi(",
    "getBandi ",
    "apiUrl",
    "api_url",
    "bandiUrl",
    "bandi_url",
    "endpoint",
    "JSON.stringify",
    "entiRiferimento",
    "enteRiferimento",
    "dataScadenza",
]


def scarica_script():
    try:
        risposta = requests.get(
            URL_SCRIPT,
            headers=INTESTAZIONI,
            timeout=30,
        )
        risposta.raise_for_status()
        return risposta.text

    except requests.RequestException as errore:
        print("Errore durante il download dello script InPA")
        print(f"Dettaglio: {errore}")
        return None


def mostra_occorrenze(testo, termine):
    testo_minuscolo = testo.lower()
    termine_minuscolo = termine.lower()
    posizione_iniziale = 0
    numero = 0

    while True:
        posizione = testo_minuscolo.find(
            termine_minuscolo,
            posizione_iniziale,
        )

        if posizione == -1:
            break

        numero += 1

        inizio = max(0, posizione - 500)
        fine = min(
            len(testo),
            posizione + len(termine) + 1000,
        )

        frammento = testo[inizio:fine]
        frammento = " ".join(frammento.split())

        print()
        print(f"Occorrenza {numero}")
        print(frammento)

        posizione_iniziale = posizione + len(termine)

    if numero == 0:
        print("Nessuna occorrenza trovata.")

    return numero


def cerca_url_api(testo):
    modelli = [
        r"https?://[^\s\"'<>]+",
        r"/wp-json/[^\s\"'<>]+",
        r"/wp-admin/admin-ajax\.php",
        r"/api/[^\s\"'<>]+",
    ]

    risultati = []

    for modello in modelli:
        for valore in re.findall(modello, testo):
            valore = valore.rstrip("),;]}")

            if valore not in risultati:
                risultati.append(valore)

    print()
    print("URL ed endpoint individuati:")
    
    if not risultati:
        print("Nessun URL o endpoint individuato.")
        return

    for valore in risultati:
        print(f"- {valore}")


def analizza_script():
    print("Ricerca chiamata API InPA")
    print()

    testo = scarica_script()

    if testo is None:
        return

    print(f"Dimensione script: {len(testo)} caratteri")

    cerca_url_api(testo)

    for termine in TERMINI:
        print()
        print("=" * 60)
        print(f"RICERCA: {termine}")
        print("=" * 60)

        mostra_occorrenze(testo, termine)

    print()
    print("Analisi mirata completata.")


if __name__ == "__main__":
    analizza_script()
