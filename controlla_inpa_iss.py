import re

import requests


URL_INPA = "https://www.inpa.gov.it/bandi-e-avvisi/"

INTESTAZIONI = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; lavoro-indeterminato-biomed-roma/1.0)"
    )
}


def controlla_configurazione_inpa():
    print("Ricerca configurazione API InPA")
    print()

    try:
        risposta = requests.get(
            URL_INPA,
            headers=INTESTAZIONI,
            timeout=30,
        )
        risposta.raise_for_status()

    except requests.RequestException as errore:
        print("Impossibile leggere la pagina InPA.")
        print(f"Dettaglio: {errore}")
        return

    testo = risposta.text

    modelli = [
        r"var\s+inpaVars\s*=\s*(\{.*?\});",
        r"inpaVars\s*=\s*(\{.*?\});",
        r'"apiurl"\s*:\s*"([^"]+)"',
        r"'apiurl'\s*:\s*'([^']+)'",
        r"apiurl\s*:\s*[^'\"]+['\"]",
    ]

    risultati = []

    for modello in modelli:
        corrispondenze = re.findall(
            modello,
            testo,
            flags=re.DOTALL | re.IGNORECASE,
        )

        for valore in corrispondenze:
            valore = " ".join(valore.split())

            if valore not in risultati:
                risultati.append(valore)

    if risultati:
        print("Configurazioni potenzialmente utili:")

        for numero, valore in enumerate(
            risultati,
            start=1,
        ):
            print()
            print(f"Risultato {numero}")
            print(valore)
    else:
        print(
            "Il valore apiurl non è stato trovato "
            "direttamente nella pagina."
        )

    posizione = testo.lower().find("inpavars")

    if posizione != -1:
        inizio = max(0, posizione - 500)
        fine = min(len(testo), posizione + 1500)

        frammento = testo[inizio:fine]
        frammento = " ".join(frammento.split())

        print()
        print("Frammento contenente inpaVars:")
        print(frammento)
    else:
        print()
        print("La stringa inpaVars non compare nella pagina.")

    print()
    print("Ricerca completata.")


if __name__ == "__main__":
    controlla_configurazione_inpa()
