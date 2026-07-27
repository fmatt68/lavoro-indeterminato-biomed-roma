import requests
from bs4 import BeautifulSoup


URL_ISS = "https://www.iss.it/at-bandi-di-concorso"

FRASI_OBBLIGATORIE = [
    "tempo indeterminato",
]

FRASI_ESCLUSE = [
    "tempo determinato",
    "dirigente medico",
    "medico chirurgo",
    "abilitazione alla professione di medico",
    "iscrizione all'ordine dei medici",
    "borsa di studio",
    "assegno di ricerca",
    "collaborazione",
]


def posizione_ammessa(testo):
    testo = testo.lower()

    contratto_valido = any(
        frase in testo for frase in FRASI_OBBLIGATORIE
    )

    esclusione_presente = any(
        frase in testo for frase in FRASI_ESCLUSE
    )

    return contratto_valido and not esclusione_presente


def controlla_iss():
    print("Controllo dei concorsi ISS in corso...")

    risposta = requests.get(URL_ISS, timeout=30)
    risposta.raise_for_status()

    pagina = BeautifulSoup(risposta.text, "html.parser")
    risultati = []

    for collegamento in pagina.find_all("a", href=True):
        titolo = collegamento.get_text(" ", strip=True)

        if titolo and posizione_ammessa(titolo):
            risultati.append(
                {
                    "titolo": titolo,
                    "link": collegamento["href"],
                }
            )

    if not risultati:
        print("Nessuna posizione ISS verificabile trovata.")
        return

    print(f"Posizioni ISS trovate: {len(risultati)}")

    for posizione in risultati:
        print()
        print(posizione["titolo"])
        print(posizione["link"])


if __name__ == "__main__":
    controlla_iss()
