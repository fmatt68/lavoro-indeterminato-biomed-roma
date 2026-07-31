import requests
import re

URL = "https://www.inpa.gov.it/bandi-e-avvisi/"

risposta = requests.get(
    URL,
    headers={
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; lavoro-indeterminato-biomed-roma)"
        )
    },
    timeout=30,
)

print("STATUS:", risposta.status_code)
print()

for risultato in re.findall(
    r'https?://[^"\'> ]+',
    risposta.text,
):
    print(risultato)
