import json, os, re, requests
from bs4 import BeautifulSoup

STORE_ID = "025"  # Westmont, IL
TOPIC = "trevor-filament-8342"
SEARCHES = ["ASA filament", "PLA filament", "PETG filament"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SEEN_FILE = "seen.json"

seen = json.load(open(SEEN_FILE)) if os.path.exists(SEEN_FILE) else {}
current = {}
alerts = []

for term in SEARCHES:
    url = "https://www.microcenter.com/search/search_results.aspx"
    params = {"Ntt": term, "storeid": STORE_ID, "myStore": "true"}
    r = requests.get(url, params=params, headers=HEADERS,
                     cookies={"storeSelected": STORE_ID}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for item in soup.select(".product_wrapper"):
        link = item.select_one("a[data-name]")
        if not link:
            continue
        name = link["data-name"]
        prices = {float(p) for p in re.findall(r"\$(\d+\.\d{2})", item.get_text())}
        if len(prices) >= 2:
            sale, regular = min(prices), max(prices)
            current[name] = sale
            if seen.get(name) != sale:
                alerts.append(f"{name}: ${sale:.2f} (was ${regular:.2f})")

if alerts:
    requests.post(f"https://ntfy.sh/{TOPIC}",
                  data="\n".join(alerts[:15]).encode(),
                  headers={"Title": "Micro Center filament sale!"})

json.dump(current, open(SEEN_FILE, "w"), indent=2)
print(f"{len(current)} on sale, {len(alerts)} new alerts")
