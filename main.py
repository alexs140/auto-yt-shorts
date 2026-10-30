import os, sys, requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
if not GEMINI_KEY or not PEXELS_KEY:
    sys.exit("ERROR: GEMINI_API_KEY ba PEXELS_API_KEY secret missing")

# Gemini (fixed model, REST call - no old library)
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
prompt = "Give me 1 crazy trending scientific fact for YouTube Shorts in Odia/English mix under 30 words. Last line: KEYWORD: <one english word for video search>"
r = requests.post(url, headers={"x-goog-api-key": GEMINI_KEY}, json={"contents":[{"parts":[{"text":prompt}]}]}, timeout=60)
if r.status_code != 200:
    sys.exit(f"GEMINI ERROR {r.status_code}: {r.text[:300]}")
text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
print("--- GENERATED SCRIPT ---"); print(text)

kw = "science"
for line in text.splitlines():
    if line.upper().startswith("KEYWORD:"):
        kw = line.split(":",1)[1].strip() or kw

p = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": PEXELS_KEY},
                 params={"query": kw, "per_page": 1, "orientation": "portrait"}, timeout=60)
if p.status_code != 200:
    sys.exit(f"PEXELS ERROR {p.status_code}: {p.text[:300]}")
v = p.json().get("videos") or []
print("--- FETCHED VIDEO URL ---")
print(v[0]["video_files"][0]["link"] if v else "no video found for " + kw)
