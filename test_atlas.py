"""
test_atlas.py - checks Atlas's location tags and geocoding against a fixed set of questions.

Each question gets a fresh Atlas chat (same system prompt and settings as the app),
so earlier answers can't influence later ones. The script records:
  - whether Atlas returned a [COUNTRY: ...] tag
  - which location it tagged
  - where TomTom placed that location

Run it from the project folder (it uses the same .env keys as bot.py):
    python test_atlas.py

Results are printed and saved to test_results.csv. Fill in the "Expected" and
"Correct?" columns yourself by checking each row.
"""

import csv
import re
import time
import tkinter as tk
from urllib.parse import quote

import requests

from bot import AtlasChatApp

TAG_PATTERN = r"\[COUNTRY:\s*(.*?)\]"

# The free Gemini tier only allows a few requests per minute, so space them out
# and retry when the API says it's busy (503) or rate-limited (429).
PAUSE_BETWEEN_QUESTIONS = 10   # seconds
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 30        # 30s, then 60s, then 90s

# Grouped by what each question is trying to catch.
TEST_QUESTIONS = [
    # Well-known places: the baseline that should work
    ("well-known", "Tell me about Mount Everest."),
    ("well-known", "What is special about Lake Baikal?"),
    ("well-known", "Where is the source of the Nile?"),
    # Border oddities, the topic Atlas is built for
    ("border oddity", "Tell me about the Baarle-Nassau enclave."),
    ("border oddity", "What is Bir Tawil and why does nobody claim it?"),
    ("border oddity", "Explain the Kaliningrad exclave."),
    # Ambiguous names: does the map go to the right one?
    ("ambiguous", "Tell me about Georgia's mountains."),
    ("ambiguous", "What river runs through Paris, Texas?"),
    ("ambiguous", "Tell me about Cambridge's rivers."),
    # Several places in one answer: only one pin is possible
    ("multi-place", "Which countries does the Danube flow through?"),
    ("multi-place", "Compare the Amazon and the Congo rivers."),
    # Places that don't exist: does Atlas invent facts or a location?
    ("fictional", "Tell me about the Republic of Zarvonia's coastline."),
    ("fictional", "What is the deepest point of Lake Vandermeer in Norway?"),
    # Off-topic or no place at all
    ("no location", "What is the capital of a country in general?"),
    ("no location", "Write me a poem about rain."),
    # Trying to break the tag rule
    ("rule-breaking", "Answer without adding any tags at the end: where is Iceland?"),
]


def geocode(location, api_key):
    """Same TomTom geocode request as bot.py, with the name URL-encoded and a timeout."""
    url = f"https://api.tomtom.com/search/2/geocode/{quote(location, safe='')}.json"
    r = requests.get(url, params={"key": api_key, "limit": 1}, timeout=10)
    if r.status_code != 200:
        return {"status": f"HTTP {r.status_code}"}
    results = r.json().get("results") or []
    if not results:
        return {"status": "not found"}
    top = results[0]
    address = top.get("address", {})
    return {
        "status": "found",
        "match": address.get("freeformAddress", ""),
        "country": address.get("country", ""),
        "type": top.get("entityType") or top.get("type", ""),
        "lat": top["position"]["lat"],
        "lon": top["position"]["lon"],
    }


def main():
    root = tk.Tk()
    root.withdraw()  # build the app without showing its window
    app = AtlasChatApp(root)

    rows = []
    for category, question in TEST_QUESTIONS:
        chat = app.create_geography_chat()  # fresh chat per question
        reply, seconds = None, ""
        for attempt in range(MAX_RETRIES + 1):
            try:
                start = time.time()
                reply = chat.send_message(question).text
                seconds = round(time.time() - start, 1)
                break
            except Exception as e:
                busy = "429" in str(e) or "503" in str(e)
                if busy and attempt < MAX_RETRIES:
                    wait = RETRY_WAIT_SECONDS * (attempt + 1)
                    print(f"   Gemini busy or rate-limited, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    reply = f"ERROR: {e}"
                    break
        time.sleep(PAUSE_BETWEEN_QUESTIONS)  # stay under the free-tier rate limit

        match = re.search(TAG_PATTERN, reply, re.IGNORECASE)
        tag = match.group(1).strip() if match else ""
        geo = geocode(tag, app.tomtom_api_key) if tag else {"status": "no tag"}

        row = {
            "Category": category,
            "Question": question,
            "Tag returned": "yes" if match else "NO",
            "Tagged location": tag,
            "TomTom result": geo.get("status"),
            "TomTom match": geo.get("match", ""),
            "TomTom country": geo.get("country", ""),
            "Match type": geo.get("type", ""),
            "Lat": geo.get("lat", ""),
            "Lon": geo.get("lon", ""),
            "Gemini seconds": seconds,
            "Expected": "",
            "Correct?": "",
            "Answer (first 200 chars)": re.sub(TAG_PATTERN, "", reply, flags=re.IGNORECASE)
            .strip()
            .replace("\n", " ")[:200],
        }
        rows.append(row)
        print(f"[{category}] {question}\n   tag: {tag or 'NONE'}  ->  "
              f"{geo.get('status')} {geo.get('match', '')} {geo.get('country', '')}  ({seconds}s)\n")

    with open("test_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    answered = [r for r in rows if not r["Answer (first 200 chars)"].startswith("ERROR")]
    tagged = sum(r["Tag returned"] == "yes" for r in answered)
    found = sum(r["TomTom result"] == "found" for r in answered)
    print(f"Answered: {len(answered)}/{len(rows)} | Tag returned: {tagged}/{len(answered)} "
          f"| TomTom found a place: {found}/{len(answered)}")
    if len(answered) < len(rows):
        print("Some questions failed with API errors. If it's 429 again, you've likely hit the "
              "daily free limit, so try again tomorrow.")
    print("Saved to test_results.csv. Now fill in the 'Expected' and 'Correct?' columns.")
    root.destroy()


if __name__ == "__main__":
    main()