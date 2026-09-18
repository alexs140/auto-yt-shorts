import os
import requests
import google.generativeai as genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

genai.configure(api_key=GEMINI_KEY)

def generate_short_content():
    try:
        # 1. Generate Script using standard Gemini Flash model
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = "Give me 1 crazy trending scientific fact for YouTube Shorts in Odia/English mix under 30 words with 1 keyword for video search."
        response = model.generate_content(prompt)
        
        print("--- GENERATED SCRIPT ---")
        print(response.text)

        # 2. Fetch Stock Video from Pexels
        headers = {"Authorization": PEXELS_KEY}
        url = "https://api.pexels.com/videos/search?query=nature&per_page=1&orientation=portrait"
        res = requests.get(url, headers=headers).json()
        
        if res.get('videos') and len(res['videos']) > 0:
            video_url = res['videos'][0]['video_files'][0]['link']
            print("--- FETCHED VIDEO URL ---")
            print(video_url)
        else:
            print("Pexels response:", res)

    except Exception as e:
        print("ERROR DETAILS:", str(e))
        raise e

if __name__ == "__main__":
    generate_short_content()
        
        
        
  
