import os, sys, time, random, requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
if not GEMINI_KEY or not PEXELS_KEY:
    sys.exit("ERROR: GEMINI_API_KEY ba PEXELS_API_KEY secret missing")

BASE = "https://generativelanguage.googleapis.com/v1beta"
PROMPT = ("Give me 1 crazy trending scientific fact for YouTube Shorts in Odia/English mix under 30 words. "
          "Last line: KEYWORD: <one english word for video search>")
# Preferred models, tried in order. If one is retired (404/400), the next is used,
# then any other flash model the key can see (from ListModels).
MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3-flash",
          "gemini-2.5-flash", "gemini-flash-lite-latest"]
BACKOFF = [2, 5, 10, 20]          # waits between attempts (4 retries)
RETRY_CODES = {408, 429, 500, 502, 503, 504}
GEMINI_BUDGET_S = 480             # stop trying Gemini after ~8 min total, use fallback fact

FALLBACK_FACTS = [
    ("Octopus ra 3 ta heart achhi aau blue blood! Two hearts pump blood to the gills, one to the body.", "octopus"),
    ("Venus re gote din eka barsa thu lamba: 1 day = 243 Earth days, 1 year = 225 days.", "venus"),
    ("Honey kebe kharap hue nahi: 3000 barsa purana honey Egypt pyramid re khaiba jogya milithila.", "honey"),
    ("Lightning ra temperature Sun ra surface thu 5 guna adhika garam, about 30,000 degree Celsius.", "lightning"),
    ("Banana radioactive! Potassium-40 thiba pain, kintu 10 million banana khaile bi danger nahi.", "banana"),
]


def request_with_retry(name, method, url, deadline=None, **kw):
    """Returns a Response, or None after all retries on network/5xx/429 errors."""
    last = None
    timeout = kw.pop("timeout", 60)
    for attempt in range(len(BACKOFF) + 1):
        if deadline and time.time() > deadline:
            print(f"[{name}] time budget used up")
            return None
        try:
            r = requests.request(method, url, timeout=timeout, **kw)
            if r.status_code not in RETRY_CODES:
                return r
            last = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        if attempt < len(BACKOFF):
            wait = BACKOFF[attempt]
            print(f"[{name}] attempt {attempt + 1} failed ({last}); retrying in {wait}s")
            time.sleep(wait)
    print(f"[{name}] gave up after {len(BACKOFF) + 1} attempts: {last}")
    return None


def list_flash_models():
    r = request_with_retry("gemini-listmodels", "GET", f"{BASE}/models?pageSize=200",
                           headers={"x-goog-api-key": GEMINI_KEY})
    if r is None or r.status_code != 200:
        return []
    out = []
    for m in r.json().get("models", []):
        n = m.get("name", "").replace("models/", "")
        if "flash" in n and "generateContent" in m.get("supportedGenerationMethods", []) \
                and not any(x in n for x in ("tts", "image", "live", "audio", "embedding")):
            out.append(n)
    return out


def gemini_fact():
    tried, candidates, listed = set(), list(MODELS), False
    deadline = time.time() + GEMINI_BUDGET_S
    while candidates and time.time() < deadline:
        model = candidates.pop(0)
        if model in tried:
            continue
        tried.add(model)
        r = request_with_retry(f"gemini:{model}", "POST", f"{BASE}/models/{model}:generateContent", deadline=deadline, timeout=90,
                               headers={"x-goog-api-key": GEMINI_KEY},
                               json={"contents": [{"parts": [{"text": PROMPT}]}]})
        if r is None:
            continue  # this model kept failing with transient errors; try the next one
        if r.status_code == 200:
            try:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                print(f"[gemini] model used: {model}")
                return text
            except (KeyError, IndexError, ValueError) as e:
                print(f"[gemini:{model}] unexpected response ({e}): {r.text[:200]}")
                continue
        print(f"[gemini:{model}] HTTP {r.status_code}: {r.text[:300]}")
        if r.status_code in (401, 403) or "API_KEY_INVALID" in r.text:
            print("[gemini] API key problem (401/403) - check the GEMINI_API_KEY secret.")
            break
        if r.status_code in (400, 404) and not listed:
            listed = True
            extra = [m for m in list_flash_models() if m not in tried and m not in candidates]
            if extra:
                print(f"[gemini] other flash models available: {extra[:6]}")
            candidates += extra[:6]
    return None


text = gemini_fact()
if not text:
    fact, kw0 = random.choice(FALLBACK_FACTS)
    text = f"{fact}\nKEYWORD: {kw0}"
    print("[gemini] failed - using a built-in fallback fact so the run still completes")
    print("::warning::Gemini failed today - a built-in fallback fact was used (see log above)")
print("--- GENERATED SCRIPT ---"); print(text)

kw = "science"
for line in text.splitlines():
    if line.strip().upper().startswith("KEYWORD:"):
        kw = line.split(":", 1)[1].strip().strip("*").strip() or kw

p = request_with_retry("pexels", "GET", "https://api.pexels.com/videos/search",
                       headers={"Authorization": PEXELS_KEY},
                       params={"query": kw, "per_page": 1, "orientation": "portrait"})
print("--- FETCHED VIDEO URL ---")
if p is None or p.status_code != 200:
    detail = "no response" if p is None else f"HTTP {p.status_code}: {p.text[:200]}"
    print(f"[pexels] could not fetch a video ({detail}); skipping video link today")
    print("::warning::Pexels failed today - no video link (see log above)")
else:
    try:
        v = p.json().get("videos") or []
        print(v[0]["video_files"][0]["link"] if v else "no video found for " + kw)
    except (ValueError, KeyError, IndexError) as e:
        print(f"[pexels] unexpected response ({e}); skipping video link today")
print("--- DONE ---")
