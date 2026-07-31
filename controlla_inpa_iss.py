import csv
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests


API_BASE = (
    "https://portale.inpa.gov.it/"
    "concorsi-smart/api/concorso-public-area/"
    "search-better"
)

FILE_ESCLUSIONI = Path("data/posizioni-escluse.csv")
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
    "rapporto di lavoro a tempo indeterminato",
]

FRASI_CONTRATTUALI_ESCLUSE = [
    "tempo determinato",
    "a tempo determinato",
    "contratto a termine",
    "borsa di studio",
    "borsa di ricerca",
    "assegno di ricerca",
    "tirocinio",
    "stage",
    "fellowship",
]

FRASI_PROCEDURALI_ESCLUSE = [
    "concorso riservato",
    "procedura riservata",
    "procedura selettiva per la trasformazione",
    "trasformazione di contratti",
    "trasformazione di contratti o assegni",
]

FRASI_PROFILI_ESCLUSI = [
    "funzionario di amministrazione",
    "dirigente amministrativo",
    "area amministrativa",
    "dirigente medico",
    "medico chirurgo",
]


def normalizza_testo(testo):
    if testo is None:
        return ""

    testo = unicodedata.normalize(
        "NFKD",
        str(testo),
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


def estrai_codice(testo):
    testo = " ".join(str(testo).upper().split())

    modelli = [
        r"\bTI\s+[A-Z0-9-]+\s+[A-Z0-9-]+\s+\d{4}\s+\d{2}\b",
        r"\bTI\s+[A-Z0-9-]+\s+\d{4}\s+\d{2}\b",
        r"\bMOB\s+[A-Z0-9-]+\s+[A-Z0-9-]+\s+\d{4}\s+\d{2}\b",
    ]

    for modello in modelli:
        risultato = re.search(modello, testo)

        if risultato:
            return " ".join(
                risultato.group(0).split()
            )

    return None


def converti_data_iso(valore):
    if not valore:
        return None

    try:
        valore = str(valore).replace("Z", "+00:00")
        return datetime.fromisoformat(valore)
    except ValueError:
        return None


def carica_codici_esclusi():
    codici = set()

    if not FILE_ESCLUSIONI.exists():
        print(
            "Avviso: data/posizioni-escluse.csv "
            "non è stato trovato."
        )
        return codici

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
                    codici.add(
                        " ".join(codice.split())
                    )

    except (OSError, csv.Error) as errore:
        print(
            "Avviso: impossibile leggere "
            "il registro delle esclusioni."
        )
        print(f"Dettaglio: {errore}")

    return codici


def appartiene_a_iss(elemento):
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

    return "istituto superiore di sanita" in testo_enti


def contratto_indeterminato(elemento):
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

    testo = normalizza_testo(
        f"{titolo} {descrizione}"
    )

    frase_ammessa = any(
        frase in testo
        for frase in FRASI_TEMPO_INDETERMINATO
    )

    frase_esclusa = any(
        frase in testo
        for frase in FRASI_CONTRATTUALI_ESCLUSE
    )

    return frase_ammessa and not frase_esclusa


def procedura_aperta(elemento):
    scadenza = estrai_valore(
        elemento,
        ["dataScadenza", "expirationDate"],
    )

    data_scadenza = converti_data_iso(scadenza)

    if data_scadenza is None:
        return False

    if data_scadenza.tzinfo is None:
        data_scadenza = data_scadenza.replace(
            tzinfo=timezone.utc
        )

    return data_scadenza >= datetime.now(timezone.utc)


def motivo_esclusione_automatica(elemento):
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

    testo = normalizza_testo(
        f"{titolo} {descrizione}"
    )

    for frase in FRASI_PROCEDURALI_ESCLUSE:
        if frase in testo:
            return f"Procedura non aperta al pubblico: {frase}"

    for frase in FRASI_PROFILI_ESCLUSI:
        if frase in testo:
            return f"Profilo non pertinente: {frase}"

    return None


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
            "Errore nel download della pagina "
            f"{numero_pagina + 1}."
        )
        print(f"Dettaglio: {errore}")
        return None

    except ValueError:
        print(
            "InPA non ha restituito dati JSON validi."
        )
        return None


def scarica_tutti_i_risultati():
    risultati_completi = []
    pagina = 0
    totale_pagine = None
    totale_dichiarato = 0

    while totale_pagine is None or pagina < totale_pagine:
        dati = scarica_pagina(pagina)

        if dati is None:
            break

        risultati[ 0
_pagine = None
_dichiarato = 0
totale_pagine = dati.get("totalPages", 0)
        totale_dichiarato = dati.get(
            "totalElements",
            totale_dichiarato,
        )

        risultati_completi.extend(risultati)
        pagina += 1

        if pagina < totale_pagine:
            time.sleep(1)

    return (
        risultati_completi,
        totale_dichiarato,
        totale_pagine or 0,
    )


def elimina_duplicati(risultati):
    risultati_unici = []
    identificativi_visti = set()

    for elemento in risultati:
        identificativo = estrai_valore(
            elemento,
            ["id", "concorsoId", "concorso_id"],
        )

        titolo = estrai_valore(
            elemento,
            ["titolo", "title"],
            "",
        )

        chiave = identificativo or normalizza_testo(titolo)

        if chiave in identificativi_visti:
            continue

        identificativi_visti.add(chiave)
        risultati_unici.append(elemento)

    return risultati_unici


def stampa_procedura(elemento, numero):
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

    codice = estrai_codice(titolo)

    scadenza_originale = estrai_valore(
        elemento,
        ["dataScadenza", "expirationDate"],
    )

    scadenza = converti_data_iso(scadenza_originale)

    print()
    print(f"Nuova procedura {numero}")
    print(f"Codice: {codice or 'Non rilevato'}")

    if scadenza:
        print(
            "Scadenza: "
            f"{scadenza.strftime('%d/%m/%Y %H:%M')}"
        )
    else:
        print("Scadenza: non rilevata")

    print(f"Titolo: {titolo}")
    print(f"ID InPA: {identificativo}")

    if identificativo != "Non disponibile":
        print(
            "Pagina InPA: "
            "https://www.inpa.gov.it/bandi-e-avvisi/"
            "dettaglio-bando-avviso/"
            f"?concorso_id={identificativo}"
        )

    print(
        "Esito: richiede verifica del PDF "
        "e dei titoli di studio."
    )


def controlla_inpa_iss():
    print(
        "Monitor incrementale dei concorsi ISS su InPA"
    )
    print()
    print(
        "Regola: esclusivamente procedure aperte "
        "a tempo indeterminato."
    )
    print()

    codici_esclusi = carica_codici_esclusi()

    risultati, totale_dichiarato, totale_pagine = (
        scarica_tutti_i_risultati()
    )

    risultati = elimina_duplicati(risultati)

    risultati_iss = [
        elemento
        for elemento in risultati
        if appartiene_a_iss(elemento)
    ]

    tempo_indeterminato = [
        elemento
        for elemento in risultati_iss
        if contratto_indeterminato(elemento)
    ]

    procedure_aperte = [
        elemento
        for elemento in tempo_indeterminato
        if procedura_aperta(elemento)
    ]

    gia_esaminate = []
    escluse[_automaticamente = ]
    nuove_procedure = []

    for elemento in procedure_aperte:
        titolo = estrai_valore(
            elemento,
            ["[ in o", "title"],
            "",
        )

        codice = estrai_codice(titolo)

        if codice and codice in codici_esclusi:
            gia_esaminate.append(elemento)
            continue

        motivo = motivo_esclusione_automatica(elemento)

        if motivo:
            escluse_automaticamente.append(
                {
                    "elemento": elemento,
                    "motivo": motivo,
                }
            )
            continue

        nuove_procedure.append(elemento)

    print()
    print("=" * 60)
    print("RIEPILOGO")
    print("=" * 60)
    print(
        "Record ISS dichiarati da InPA: "
        f"{totale_dichiarato}"
    )
    print(f"Pagine analizzate: {totale_pagine}")
    print(
        "Record ISS effettivamente scaricati: "
        f"{len(risultati_iss)}"
    )
    print(
        "Procedure a tempo indeterminato: "
        f"{len(tempo_indeterminato)}"
    )
    print(
        "Procedure ancora aperte: "
        f"{len(procedure_aperte)}"
    )
    print(
        "Procedure già controllate e ignorate: "
        f"{len(gia_esaminate)}"
    )
    print(
        "Procedure escluse automaticamente: "
        f"{len(escluse_automaticamente)}"
    )
    print(
        "Nuove procedure ISS da verificare: "
        f"{len(nuove_procedure)}"
    )

    if escluse_automaticamente:
        print()
        print("Esclusioni automatiche:")

        for voce in escluse_automaticamente:
            titolo = estrai_valore(
                voce["elemento"],
                ["titolo", "title"],
                "Titolo non disponibile",
            )

            print()
            print(f"- {titolo}")
            print(f"  Motivo: {voce['motivo']}")

    for numero, elemento in enumerate(
        nuove_procedure,
        start=1,
    ):
        stampa_procedura(elemento, numero)

    print()
    print(
        "Controllo completato. "
        "Nessun CSV è stato modificato."
    )


if __name__ == "__main__":
    controlla_inpa_iss()
