import requests
from bs4 import BeautifulSoup


URL = "https://www.inpa.gov.it/bandi-e-avvisi/"


def controlla_inpa():
    print("Controllo InPA ISS")
    print()

    try:
        risposta = requests.get(
            URL,
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; lavoro-indeterminato-biomed-roma)"
                )
            },
        )

        risposta.raise_for_status()

    except Exception as errore:
        print("Errore durante il collegamento a InPA")
        print(errore)
        return

    pagina = BeautifulSoup(
        risposta.text,
        "html.parser",
    )

    testo = pagina.get_text(
        " ",
        strip=True,
    )

    print(
        f"Lunghezza del testo scaricato: "
        f"{len(testo)} caratteri"
    )

    print()

    if "istituto superiore di sanita" in testo.lower():
        print(
            "Riferimento a ISS individuato."
        )
    else:
        print(
            "Nessun riferimento ISS "
            "trovato automaticamente."
        )

    print()
    print("Test InPA completato.")


if __name__ == "__main__":
    controlla_inpa()
