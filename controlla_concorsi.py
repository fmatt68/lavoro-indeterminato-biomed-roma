import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


URL_ISS = "https://www.iss.it/at-bandi-di-concorso"

FRASI_TEMPO_INDETERMINATO = [
    "tempo indeterminato",
    "a tempo indeterminato",
]

FRASI_ESCLUSE = [
    "non a tempo indeterminato",
    "personale non a tempo indeterminato",
    "funzionario di amministrazione",
    "profilo amministrativo",
    "concorso riservato",
    "tempo determinato",
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

FRASI_BANDO_CHIUSO = [
    "stato: chiuso",
    "stato chiuso",
    "bando chiuso",
    "candidature chiuse",
    "termini scaduti",
    "termine scaduto",
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

INTESTAZIONI = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
    )
}


def normalizza_testo(testo):
    """Converte il testo in minuscolo e rimuove gli spazi duplicati."""
    return " ".join(testo.lower().split())


def posizione_ammessa(testo):
    """Controlla il contratto ed esclude i profili non pertinenti."""
    testo_normalizzato = normalizza_testo(testo)

    contratto_valido = any(
        frase in testo_normalizzato
        for frase in FRASI_TEMPO_INDETERMINATO
    )

    esclusione_presente = any(
        frase in testo_normalizzato
        for frase in FRASI_ESCLUSE
    )

    return contratto_valido and not esclusione_presente


def estrai_data_scadenza(testo):
    """Cerca nel testo una data di chiusura numerica o testuale."""
    testo_normalizzato = normalizza_testo(testo)

    modello_numerico = re.search(
        r"(?:data chiusura candidature|scadenza)"
        r"[:\s]+"
        r"(\d{1,2})\d{1,2}\d{4}",
        testo_normalizzato,
    )

    if modello_numerico:
        giorno = int(modello_numerico.group(1))
        mese = int(modello_numerico.group(2))
        anno = int(modello_numerico.group(3))

        try:
            return datetime(anno, mese, giorno).date()
        except ValueError:
            return None

    modello_testuale = re.search(
        r"(?:data chiusura candidature|scadenza)"
        r"[:\s]+"
        r"(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|"
        r"luglio|agosto|settembre|ottobre|novembre|dicembre)"
        r"\s+(\d{4})",
        testo_normalizzato,
    )

    if modello_testuale:
        giorno = int(modello_testuale.group(1))
        mese = MESI_ITALIANI[modello_testuale.group(2)]
        anno = int(modello_testuale.group(3))

        try:
            return datetime(anno, mese, giorno).date()
        except ValueError:
            return None

    return None


def scarica_pagina(url):
    """Scarica una pagina senza interrompere il programma in caso di errore."""
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


def trova_link_inpa(link_iss):
    """Cerca un collegamento InPA nella pagina ISS del concorso."""
    risposta = scarica_pagina(link_iss)

    if risposta is None:
        return None

    dominio_finale = urlparse(risposta.url).netloc.lower()

    if "inpa.gov.it" in dominio_finale:
        return risposta.url

    pagina = BeautifulSoup(risposta.text, "html.parser")

    for collegamento in pagina.find_all("a", href=True):
        link = urljoin(risposta.url, collegamento["href"])
        dominio = urlparse(link).netloc.lower()

        if "inpa.gov.it" in dominio:
            return link

    risultato = re.search(
        r"https?://(?:www\.)?inpa\.gov\.it/[^\s\"'<>]+",
        risposta.text,
    )

    if risultato:
        return risultato.group(0)

    return None


def controlla_stato_bando(link_iss):
    """Controlla stato e scadenza sulla pagina InPA, quando disponibile."""
    link_inpa = trova_link_inpa(link_iss)

    if not link_inpa:
        return {
            "stato": "da_verificare",
            "scadenza": None,
            "link_verifica": link_iss,
        }

    risposta = scarica_pagina(link_inpa)

    if risposta is None:
        return {
            "stato": "da_verificare",
            "scadenza": None,
            "link_verifica": link_inpa,
        }

    pagina = BeautifulSoup(risposta.text, "html.parser")
    testo = normalizza_testo(
        pagina.get_text(" ", strip=True)
    )

    scadenza = estrai_data_scadenza(testo)

    if any(frase in testo for frase in FRASI_BANDO_CHIUSO):
        return {
            "stato": "chiuso",
            "scadenza": scadenza,
            "link_verifica": risposta.url,
        }

    if scadenza and scadenza < datetime.now().date():
        return {
            "stato": "scaduto",
            "scadenza": scadenza,
            "link_verifica": risposta.url,
        }

    if scadenza:
        return {
            "stato": "aperto",
            "scadenza": scadenza,
            "link_verifica": risposta.url,
        }

    return {
        "stato": "da_verificare",
        "scadenza": None,
        "link_verifica": risposta.url,
    }


def controlla_iss():
    """Trova i possibili concorsi ISS a tempo indeterminato."""
    print("Controllo dei concorsi ISS in corso...")

    risposta = scarica_pagina(URL_ISS)

    if risposta is None:
        print("Il controllo ISS non può essere completato.")
        return

    pagina = BeautifulSoup(risposta.text, "html.parser")
    risultati = []
    elementi_gia_visti = set()

    for collegamento in pagina.find_all("a", href=True):
        contenitore = collegamento.find_parent(
            ["article", "li", "div", "section"]
        )

        if contenitore:
            testo = contenitore.get_text(" ", strip=True)
        else:
            testo = collegamento.get_text(" ", strip=True)

        testo = " ".join(testo.split())

        if not testo:
            continue

        if not posizione_ammessa(testo):
            continue

        link_iss = urljoin(URL_ISS, collegamento["href"])

        chiave = normalizza_testo(testo)

        if chiave in elementi_gia_visti:
            continue

        elementi_gia_visti.add(chiave)

        verifica = controlla_stato_bando(link_iss)

        risultati.append(
            {
                "titolo": testo,
                "link_iss": link_iss,
                "link_verifica": verifica["link_verifica"],
                "stato": verifica["stato"],
                "scadenza": verifica["scadenza"],
            }
        )

    risultati_utili = [
        risultato
        for risultato in risultati
        if risultato["stato"] not in ["chiuso", "scaduto"]
    ]

    risultati_esclusi = [
        risultato
        for risultato in risultati
        if risultato["stato"] in ["chiuso", "scaduto"]
    ]

    print()
    print(
        "Possibili concorsi ISS da verificare: "
        f"{len(risultati_utili)}"
    )

    for numero, posizione in enumerate(
        risultati_utili,
        start=1,
    ):
        print()
        print(f"Risultato {numero}")
        print(f"Stato: {posizione['stato']}")

        if posizione["scadenza"]:
            scadenza_formattata = posizione[
                "scadenza"
            ].strftime("%d/%m/%Y")

            print(f"Scadenza: {scadenza_formattata}")
        else:
            print("Scadenza: non rilevata automaticamente")

        print(posizione["titolo"])
        print(f"Fonte ISS: {posizione['link_iss']}")
        print(
            "Pagina di verifica: "
            f"{posizione['link_verifica']}"
        )

    print()
    print(
        "Concorsi esclusi perché chiusi o scaduti: "
        f"{len(risultati_esclusi)}"
    )

    for posizione in risultati_esclusi:
        print()
        print(f"Escluso perché: {posizione['stato']}")

        if posizione["scadenza"]:
            scadenza_formattata = posizione[
                "scadenza"
            ].strftime("%d/%m/%Y")

            print(f"Scadenza: {scadenza_formattata}")

        print(posizione["titolo"])
        print(
            "Pagina di verifica: "
            f"{posizione['link_verifica']}"
        )

    print()
    print(
        "Nota: i concorsi aperti o da verificare non vengono "
        "inseriti automaticamente nel CSV. È ancora necessario "
        "controllare i titoli di studio e la pertinenza biomedica."
    )


if __name__ == "__main__":
    controlla_iss()
