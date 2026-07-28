import csv
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


URL_ISS = "https://www.iss.it/at-bandi-di-concorso"

FILE_ESCLUSIONI = Path("data/posizioni-escluse.csv")

INTESTAZIONI = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
    )
}

FRASI_ESCLUSE = [
    "non a tempo indeterminato",
    "personale non a tempo indeterminato",
    "tempo determinato",
    "funzionario di amministrazione",
    "profilo amministrativo",
    "concorso riservato",
    "dirigente medico",
    "medico chirurgo",
    "abilitazione alla professione di medico",
    "iscrizione all'ordine dei medici",
    "borsa di studio",
    "assegno di ricerca",
    "collaborazione",
    "tirocinio",
    "stage",
]

MESI_ITALIANI = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

PAGINE_INPA_CONOSCIUTE = {
    "TI DT DRUE 2026 01": (
        "https://www.inpa.gov.it/bandi-e-avvisi/"
        "dettaglio-bando-avviso/"
        "?concorso_id=ce01550874614308a37b131f9fbc9628"
    ),
    "TI DT DRAG 2026 01": (
        "https://www.inpa.gov.it/bandi-e-avvisi/"
        "dettaglio-bando-avviso/"
        "?concorso_id=b98a3e13056344d1be89d39a4178f92a"
    ),
    "TI PT DRUE 2026 01": (
        "https://www.inpa.gov.it/bandi-e-avvisi/"
        "dettaglio-bando-avviso/"
        "?concorso_id=a0b24821c41948eaaf0fc42f81559a46"
    ),
    "TI CTER CNT 2026 01": (
        "https://www.inpa.gov.it/bandi-e-avvisi/"
        "dettaglio-bando-avviso/"
        "?concorso_id=8a93759556604f1d9a1831cadd496632"
    ),
    "TI DR CNS 2026 01": (
        "https://www.inpa.gov.it/bandi-e-avvisi/"
        "dettaglio-bando-avviso/"
        "?concorso_id=7eebbbf678ed440e8b277ecb688fc041"
    ),
}


def normalizza_testo(testo):
    return " ".join(testo.lower().split())


def scarica_pagina(url):
    try:
        risposta = requests.get(
            url,
            headers=INTESTAZIONI,
            timeout=30,
            allow_redirects=True,
        )
        risposta.raise_for_status()
        return risposta
    except requests.RequestException as errore:
        print(f"Avviso: impossibile aprire {url}")
        print(f"Dettaglio tecnico: {errore}")
        return None


def carica_codici_esclusi():
    codici_esclusi = set()

    if not FILE_ESCLUSIONI.exists():
        print(
            "Avviso: il file delle esclusioni non è stato trovato."
        )
        return codici_esclusi

    try:
        with FILE_ESCLUSIONI.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as file_csv:
            lettore = csv.DictReader(file_csv)

            for riga in lettore:
                codice = riga.get("codice", "").strip().upper()

                if codice:
                    codici_esclusi.add(codice)

    except (OSError, csv.Error) as errore:
        print(
            "Avviso: impossibile leggere il file delle esclusioni."
        )
        print(f"Dettaglio tecnico: {errore}")

    return codici_esclusi


def posizione_ammessa(testo):
    testo_normalizzato = normalizza_testo(testo)

    if "tempo indeterminato" not in testo_normalizzato:
        return False

    return not any(
        frase in testo_normalizzato
        for frase in FRASI_ESCLUSE
    )


def estrai_codice_concorso(testo):
    risultato = re.search(
        r"\bTI\s+[A-Z]+\s+[A-Z]+\s+\d{4}\s+\d{2}\b",
        testo.upper(),
    )

    if risultato:
        return " ".join(risultato.group(0).split())

    return None


def estrai_scadenza(testo):
    testo_normalizzato = normalizza_testo(testo)

    risultato = re.search(
        r"data chiusura candidature[:\s]+"
        r"(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|"
        r"luglio|agosto|settembre|ottobre|novembre|dicembre)"
        r"\s+(\d{4})",
        testo_normalizzato,
    )

    if not risultato:
        return None

    giorno = int(risultato.group(1))
    mese = MESI_ITALIANI[risultato.group(2)]
    anno = int(risultato.group(3))

    try:
        return datetime(anno, mese, giorno).date()
    except ValueError:
        return None


def controlla_pagina_inpa(url):
    risposta = scarica_pagina(url)

    if risposta is None:
        return {
            "stato": "da_verificare",
            "scadenza": None,
        }

    pagina = BeautifulSoup(risposta.text, "html.parser")
    testo = normalizza_testo(
        pagina.get_text(" ", strip=True)
    )

    scadenza = estrai_scadenza(testo)

    if "stato: chiuso" in testo or "stato chiuso" in testo:
        stato = "chiuso"
    elif scadenza and scadenza < datetime.now().date():
        stato = "scaduto"
    elif "stato: aperto" in testo or "stato aperto" in testo:
        stato = "aperto"
    elif scadenza:
        stato = "aperto"
    else:
        stato = "da_verificare"

    return {
        "stato": stato,
        "scadenza": scadenza,
    }


def trova_concorsi_iss(codici_esclusi):
    risposta = scarica_pagina(URL_ISS)

    if risposta is None:
        return [], []

    pagina = BeautifulSoup(risposta.text, "html.parser")
    nuovi_risultati = []
    gia_esaminati = []
    codici_gia_visti = set()

    for collegamento in pagina.find_all("a", href=True):
        contenitore = collegamento.find_parent(
            ["article", "li", "div", "section"]
        )

        if contenitore:
            titolo = contenitore.get_text(" ", strip=True)
        else:
            titolo = collegamento.get_text(" ", strip=True)

        titolo = " ".join(titolo.split())

        if not titolo or not posizione_ammessa(titolo):
            continue

        codice = estrai_codice_concorso(titolo)

        if not codice or codice in codici_gia_visti:
            continue

        codici_gia_visti.add(codice)

        if codice in codici_esclusi:
            gia_esaminati.append(codice)
            continue

        fonte_iss = urljoin(
            URL_ISS,
            collegamento["href"],
        )

        pagina_inpa = PAGINE_INPA_CONOSCIUTE.get(codice)

        if pagina_inpa:
            verifica = controlla_pagina_inpa(pagina_inpa)
        else:
            verifica = {
                "stato": "da_verificare",
                "scadenza": None,
            }

        nuovi_risultati.append(
            {
                "codice": codice,
                "titolo": titolo,
                "stato": verifica["stato"],
                "scadenza": verifica["scadenza"],
                "fonte_iss": fonte_iss,
                "pagina_inpa": pagina_inpa,
            }
        )

    return nuovi_risultati, gia_esaminati


def stampa_risultato(posizione, numero=None):
    print()

    if numero is not None:
        print(f"Risultato {numero}")

    print(f"Codice: {posizione['codice']}")
    print(f"Stato: {posizione['stato']}")

    if posizione["scadenza"]:
        print(
            "Scadenza: "
            f"{posizione['scadenza'].strftime('%d/%m/%Y')}"
        )
    else:
        print("Scadenza: non rilevata automaticamente")

    print(posizione["titolo"])
    print(f"Fonte ISS: {posizione['fonte_iss']}")

    if posizione["pagina_inpa"]:
        print(f"Pagina InPA: {posizione['pagina_inpa']}")
    else:
        print("Pagina InPA: non ancora associata")


def controlla_iss():
    print("Controllo dei concorsi ISS in corso...")

    codici_esclusi = carica_codici_esclusi()

    print(
        "Concorsi presenti nel registro delle esclusioni: "
        f"{len(codici_esclusi)}"
    )

    risultati, gia_esaminati = trova_concorsi_iss(
        codici_esclusi
    )

    aperti = [
        posizione
        for posizione in risultati
        if posizione["stato"] == "aperto"
    ]

    da_verificare = [
        posizione
        for posizione in risultati
        if posizione["stato"] == "da_verificare"
    ]

    chiusi_o_scaduti = [
        posizione
        for posizione in risultati
        if posizione["stato"] in ["chiuso", "scaduto"]
    ]

    print()
    print(
        "Concorsi ISS già esaminati e ignorati: "
        f"{len(gia_esaminati)}"
    )

    for codice in sorted(gia_esaminati):
        print(f"- {codice}")

    print()
    print(f"Nuovi concorsi ISS aperti: {len(aperti)}")

    for numero, posizione in enumerate(aperti, start=1):
        stampa_risultato(posizione, numero)

    print()
    print(
        "Nuovi concorsi ISS da verificare: "
        f"{len(da_verificare)}"
    )

    for numero, posizione in enumerate(
        da_verificare,
        start=1,
    ):
        stampa_risultato(posizione, numero)

    print()
    print(
        "Nuovi concorsi ISS chiusi o scaduti: "
        f"{len(chiusi_o_scaduti)}"
    )

    for posizione in chiusi_o_scaduti:
        stampa_risultato(posizione)

    print()
    print(
        "Nota: i codici presenti nel registro delle esclusioni "
        "non vengono riproposti. Gli eventuali nuovi concorsi "
        "devono essere verificati prima dell'inserimento nel CSV."
    )


if __name__ == "__main__":
    controlla_iss()
