import time
import unicodedata

import requests


API_BASE = (
    "https://portale.inpa.gov.it/"
    "concorsi-smart/api/concorso-public-area/"
    "search-better"
)

DIMENSIONE_PAGINA = 50

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
    "enteRiferimentoName": "Istituto Superiore di Sanità",
}

FRASI_TEMPO_INDETERMINATO = [
    "tempo indeterminato",
    "a tempo indeterminato",
    "contratto a tempo indeterminato",
    "assunzione a tempo indeterminato",
]

FRASI_DA_ESCLUDERE = [
    "tempo determinato",
    "a tempo determinato",
    "contratto a termine",
    "borsa di studio",
    "borsa di ricerca",
    "assegno di ricerca",
    "tirocinio",
    "stage",
    "fellowship",
    "collaborazione",
]


def normalizza_testo(testo):
    if testo is None:
        return ""

    testo = str(testo)

    testo = unicodedata.normalize(
        "NFKD",
        testo,
    )

    testo = "".join(
        carattere
        for carattere in testo
        if not unicodedata.combining(carattere)
    )

    return " ".join(testo.lower().split())


def estrai_valore(elemento, chiavi, predefinito=None):
    for chiave in chiavi:
        valore = elemento.get(chiave)

        if valore not in [None, "", []]:
            return valore

    return predefinito


def ente_iss(elemento):
    enti = estrai_valore(
        elemento,
        ["entiRiferimento", "enteRiferimento"],
        [],
    )

    if isinstance(enti, str):
        enti = [enti]

    testo_enti = normalizza_testo(
        " ".join(str(ente) for ente in enti)
    )

    riferimenti_iss = [
        "istituto superiore di sanita",
        "istituto superiore di sanita iss",
    ]

    return any(
        riferimento in testo_enti
        for riferimento in riferimenti_iss
    )


def solo_tempo_indeterminato(titolo, descrizione):
    testo = normalizza_testo(
        f"{titolo} {descrizione}"
    )

    tempo_indeterminato = any(
        frase in testo
        for frase in FRASI_TEMPO_INDETERMINATO
    )

    esclusione_presente = any(
        frase in testo
        for frase in FRASI_DA_ESCLUDERE
    )

    return tempo_indeterminato and not esclusione_presente


def scarica_pagina(numero_pagina):
    url = (
        f"{API_BASE}"
        f"?page={numero_pagina}"
        f"&size={DIMENSIONE_PAGINA}"
    )

    try:
        risposta = requests.post(
            url,
            headers=INTESTAZIONI,
            json=FILTRO_ISS,
            timeout=30,
        )

        print(
            f"Pagina {numero_pagina + 1}: "
            f"HTTP {risposta.status_code}"
        )

        risposta.raise_for_status()
        return risposta.json()

    except requests.RequestException as errore:
        print(
            "Errore durante il download della pagina "
            f"{numero_pagina + 1}."
        )
        print(f"Dettaglio: {errore}")
        return None

    except ValueError:
        print(
            "La pagina ricevuta da InPA "
            "non contiene dati JSON validi."
        )
        return None


def scarica_tutti_i_risultati():
    tutti_i_risultati = []
    pagina = 0
    totale_pagine = None

    while totale_pagine is None or pagina < totale_pagine:
        dati = scarica_pagina(pagina)

        if dati is None:
            break

        risultati = dati.get("content", [])
        totale_pagine = dati.get("totalPages", 0)
        totale_elementi = dati.get("totalElements", 0)

        if pagina == 0:
            print()
            print(
                "Risultati ISS dichiarati da InPA: "
                f"{totale_elementi}"
            )
            print(
                "Pagine da analizzare: "
                f"{totale_pagine}"
            )
            print()

        tutti_i_risultati.extend(risultati)

        pagina += 1

        if pagina < totale_pagine:
            time.sleep(1)

    return tutti_i_risultati


def filtra_tempo_indeterminato(risultati):
    risultati_filtrati = []
    identificativi_visti = set()

    for elemento in risultati:
        identificativo = estrai_valore(
            elemento,
            ["id", "concorsoId", "concorso_id"],
        )

        if identificativo in identificativi_visti:
            continue

        titolo = estrai_valore(
            elemento,
            ["titolo", "title"],
            "",
        )

        descrizione = estrai_valore(
            elemento,
            ["descrizioneBreve", "descrizione"],
            "",
        )

        if not ente_iss(elemento):
            continue

        if not solo_tempo_indeterminato(
            titolo,
            descrizione,
        ):
            continue

        if identificativo:
            identificativi_visti.add(identificativo)

        risultati_filtrati.append(elemento)

    return risultati_filtrati


def stampa_risultato(elemento, numero):
    identificativo = estrai_valore(
        elemento,
        ["id", "concorsoId", "concorso_id"],
        "Non disponibile",
    )

    titolo = estrai_valore(
        elemento,
        ["titolo", "title"],
        "Non disponibile",
    )

    enti = estrai_valore(
        elemento,
        ["entiRiferimento", "enteRiferimento"],
        "Non disponibile",
    )

    stato = estrai_valore(
        elemento,
        ["status", "stato", "descrizioneStato"],
        "Non disponibile",
    )

    pubblicazione = estrai_valore(
        elemento,
        ["dataPubblicazione", "publicationDate"],
        "Non disponibile",
    )

    scadenza = estrai_valore(
        elemento,
        ["dataScadenza", "expirationDate"],
        "Non disponibile",
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


def controlla_inpa_iss():
    print("Ricerca approfondita dei concorsi ISS su InPA")
    print()
    print(
        "Regola contrattuale: "
        "solo tempo indeterminato."
    )
    print()

    risultati = scarica_tutti_i_risultati()

    print()
    print(
        "Risultati complessivamente scaricati: "
        f"{len(risultati)}"
    )

    risultati_filtrati = filtra_tempo_indeterminato(
        risultati
    )

    print()
    print(
        "Concorsi ISS esclusivamente a tempo "
        f"indeterminato trovati: {len(risultati_filtrati)}"
    )

    for numero, elemento in enumerate(
        risultati_filtrati,
        start=1,
    ):
        stampa_risultato(elemento, numero)

    print()
    print(
        "Controllo completato. "
        "Nessun file CSV è stato modificato."
    )


if __name__ == "__main__":
    controlla_inpa_iss()
