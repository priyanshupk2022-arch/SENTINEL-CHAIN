import urllib.request
import re
import json

url = "https://www.youtube.com/watch?v=OjB6SBK_aDc"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")

    # Look for captions / captions tracks / transcript
    captions_match = re.search(r'"captionTracks":(\[.*?\])', html)
    if captions_match:
        print("Captions Found:", captions_match.group(1))
    else:
        print("No direct caption tracks in initial HTML.")

    # Search for initialData and live chat or video panels
    init_data_match = re.search(r"ytInitialData\s*=\s*({.+?});</script>", html)
    if init_data_match:
        data = json.loads(init_data_match.group(1))
        print("ytInitialData extracted successfully.")
        # Find live chat renderer or description details
        panels = str(data)[:2000]
        print("Data sample:", panels[:400])
except Exception as e:
    print("Error:", e)
