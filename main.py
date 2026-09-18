import os
import requests
import google.generativeai as genai

# Setup API Keys
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def generate_short_content():
    # 1. Generate Script
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "Give me 1 crazy trending scientific fact for YouTube Shorts in Odia/English mix under 30 words with 1 keyword for video search."
    response = model.generate_content(prompt)
    print("Generated Script:", response.text)

    # 2. Fetch Stock Video from Pexels
    headers = {"Authorization": PEXELS_KEY}
    url = "https://api.pexels.com/videos/search?query=nature&per_page=1&orientation=portrait"
    res = requests.get(url, headers=headers).json()
    if res.get('videos'):
        video_url = res['videos'][0]['video_files'][0]['link']
        print("Fetched Background Video URL:", video_url)

if __name__ == "__main__":
    generate_short_content()
  
