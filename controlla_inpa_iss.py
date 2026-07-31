import requests

URL = "https://www.inpa.gov.it/bandi-e-avvisi/"


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

print("STATUS:", risposta.status_code)
print()

print(risposta.text[:5000])
