# Atlas: Live AI Geography Guide & Mapping Bot

Atlas is an interactive desktop application built in Python that combines generative AI with live map tracking. Users can chat with "Atlas", a knowledgeable and sharp geography scholar, and watch the embedded map pan, zoom and drop a marker on the location being discussed.

## Features

* **AI Chat:** Powered by the Google Gemini API (`gemini-2.5-flash`) to deliver specific geographical facts.
* **Live Interactive Map:** Built with `tkintermapview`, using OpenStreetMap tiles.
* **Location Tag Parsing:** A regex parser picks up the location tag Atlas adds to the end of each reply and removes it before the answer is shown.
* **Geocoding Pipeline:** Uses the TomTom Geocoding API to convert place names into latitude and longitude coordinates.

## How it works

1. **Prompting.** Each question goes to Gemini 2.5 Flash with a system prompt that makes it answer as "Atlas" and end every reply with a location token in the form `[COUNTRY: Place Name]`.
2. **Parsing.** A regular expression finds the token, removes it from the reply, and shows the rest in the chat window.
3. **Geocoding.** The tagged place name is sent to the TomTom Geocoding API, which returns the coordinates of its top match.
4. **Mapping.** The map centres on those coordinates, clears the previous marker and drops a new one labelled with the place name.

## Testing

`test_atlas.py` sends a set of questions to Atlas, each in a fresh chat so earlier answers can't influence later ones. The questions are grouped to probe specific weak points: well-known places, border oddities, ambiguous names, answers covering several places, places that don't exist, and questions with no location. It records the tag Atlas returned and where TomTom placed it, and saves everything to `test_results.csv` for checking by hand.

```
python test_atlas.py
```

### Results (October 2026)

14 questions were answered and checked. Two further questions in the script (a non-geography request and an attempt to make Atlas skip its tag) hit the Gemini free tier's rate limit and are not included.

| Category | Answered | Tag returned | Right country | Pin on the place discussed |
|---|---|---|---|---|
| Well-known | 3 | 3/3 | 3/3 | 0/3 |
| Border oddity | 3 | 2/3 | 2/3 | 0/3 |
| Ambiguous name | 3 | 2/3 | 2/3 | 1/3 |
| Several places | 2 | 2/2 | 0/2 | 0/2 |
| Fictional place | 2 | 2/2 | n/a | n/a |
| No location | 1 | 1/1 (should be 0) | n/a | n/a |

### What I found

**1. Atlas tags countries, not places, so pins land in capital cities.** 11 of the 12 tags were whole countries, even when the question was about one specific place. TomTom then returns the country's reference point, which is usually its capital:

| Question about | Tagged | Pin landed in | Distance from the real place |
|---|---|---|---|
| Lake Baikal | Russia | Moscow | about 4,300 km |
| Paris, Texas | United States | Washington, D.C. | about 1,750 km |
| Kaliningrad exclave | Russia | Moscow | about 1,090 km |
| Mount Everest | Nepal | Kathmandu | about 160 km |
| Baarle-Nassau enclave | Netherlands | Amsterdam | about 100 km |

Kaliningrad is the clearest failure: the question was about a part of Russia cut off from the rest of it, and the pin went to the rest of it.

**2. The geocoder sometimes matches the wrong thing entirely.** "Danube River Basin" matched *Danube River Lane*, a street in Sacramento, California, about 9,500 km from the river. "Democratic Republic of the Congo" matched the *Republic of the Congo*, a different country, with the pin in Brazzaville. The code accepts TomTom's first result without checking its type or country, so neither error was caught.

**3. The tag rule isn't reliable in either direction.** Atlas left out the tag twice (Bir Tawil and Cambridge) despite the prompt saying "always include this token". It also added tags when there was no real place to map: a general question about capital cities was pinned to Bolivia, and both fictional places were pinned to Norway.

**4. It didn't make up the fictional places.** For both "Republic of Zarvonia" and "Lake Vandermeer", Atlas opened by saying it didn't recognise the place, rather than inventing facts about it.

**5. Ambiguous names were mixed.** "Georgia's mountains" correctly went to the country rather than the US state, but for "Cambridge" Atlas assumed the UK city without asking.

## Known limitations

- **Country-level tags.** The prompt asks for "the main country or specific city/region", and in practice Gemini almost always picks the country, so the map rarely shows the actual place discussed.
- **One location per answer.** The parser reads only the first token, so a question about the Danube's ten countries or two rivers can only show one pin.
- **No checks on the geocoding result.** TomTom is called with `limit=1` and no country hint, and whatever comes back first is shown, whether it's a country, a city or a street on another continent.
- **Same zoom for everything.** The map always zooms to level 6, which suits a country but is too far out for a city and too close for Russia.
- **Silent map failures.** If the tag is missing or TomTom finds nothing, the error is only printed to the console. The chat shows the new answer while the map still shows the previous pin.
- **Place names aren't URL-encoded.** The name goes straight into the request path, so a name containing `/`, `?` or `#` breaks the request.
- **The window freezes while waiting.** The Gemini and TomTom calls run on the main interface thread, and the TomTom request has no timeout.
- **Facts aren't checked.** Answers come straight from the model. The prompt calls Atlas's knowledge "flawless", requires a "highly specific" fact in every reply and uses a temperature of 0.8, all of which push towards confident answers.

## What I'd change next

- Ask Gemini for the most specific place discussed, plus its country (for example `[PLACE: Kaliningrad | Russia]`), and pass the country to TomTom to filter results.
- Reject geocoding results that don't fit, such as a street when a river or region was asked about, or a different country from the one tagged.
- Allow no tag when there's nothing real to map, instead of forcing one.
- Support several tags per answer and show a pin for each.
- Lower the temperature, drop "flawless" from the prompt, and let Atlas say when it isn't sure.
- Show "couldn't find this place on the map" in the chat, and run API calls in a background thread with timeouts.

## Installation & Setup

### 1. Prerequisites

Make sure you have Python installed, then install the required packages:

```
pip install google-genai tkintermapview requests
```

### 2. Clone the repository

```
git clone https://github.com/akica66/atlas-geography-ai.git
cd atlas-geography-ai
```

### 3. Add your API keys

This project keeps API keys out of the code using a `.env` file.

1. Find the `.env.example` file in the project folder.
2. Make a copy and rename it to exactly `.env`.
3. Open `.env` and paste in your own keys, with no quotes or extra spaces:

```
GEMINI_API_KEY=your_gemini_key_here
TOMTOM_API_KEY=your_tomtom_key_here
```

The `.env` file is listed in `.gitignore`, so it is never pushed to GitHub.

## How to Run

```
python bot.py
```

Type a question or name a geographic oddity (for example "Tell me about the Baarle-Nassau enclave" or "Where is the source of the Nile?") and watch the map follow along.
