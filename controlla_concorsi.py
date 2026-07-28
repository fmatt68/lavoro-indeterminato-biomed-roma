import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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


def normalizza_testo(testo):
    return " ".join(testo.lower().split())


def posizione_ammessa(testo):
    testo = normalizza_testo(testo)

    contratto_valido = any(
        frase in testo
        for frase in FRASI_TEMPO_INDETERMINATO
    )

    esclusione_presente = any(
        frase in testo
        for frase in FRASI_ESCLUSE
    )

    return contratto_valido and not esclusione_presente


def controlla_iss():
    print("Controllo dei concorsi ISS in corso...")

    intestazioni = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
        )
    }

    risposta = requests.get(
        URL_ISS,
        headers=intestazioni,
        timeout=30,
    )
    risposta.raise_for_status()

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

        if not testo or not posizione_ammessa(testo):
            continue

        link = urljoin(URL_ISS, collegamento["href"])
        chiave = (testo, link)

        if chiave in elementi_gia_visti:
            continue

        elementi_gia_visti.add(chiave)

        risultati.append(
            {
                "titolo": testo,
                "link": link,
            }
        )

    if not risultati:
        print("Nessuna posizione ISS verificabile trovata.")
        return

    print(
        f"Possibili concorsi ISS da verificare: {len(risultati)}"
    )

    for numero, posizione in enumerate(risultati, start=1):
        print()
        print(f"Risultato {numero}")
        print(posizione["titolo"])
        print(posizione["link"])

    print()
    print(
        "Nota: i risultati devono essere verificati "
        "nel bando ufficiale prima di essere inseriti nel CSV."
    )


if __name__ == "__main__":
    controlla_iss()
