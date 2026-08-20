import urllib.request
import re
import json

url = "https://www.youtube.com/watch?v=OjB6SBK_aDc"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")

    # Extract live chat continuation or messages if present
    chat_match = re.search(r'"liveChatRenderer":\s*({.+?})\s*,\s*"header"', html)
    if chat_match:
        print("Live chat renderer present")
    
    # Let's search for keywords, stream status, description, comments
    match_contents = re.findall(r'"runs":\s*(\[.*?\])', html)
    print(f"Found {len(match_contents)} text runs")
    texts = []
    for m in match_contents:
        try:
            items = json.loads(m)
            for it in items:
                t = it.get("text", "")
                if t and len(t) > 15:
                    texts.append(t)
        except:
            pass
    print("Sample texts found:")
    for t in texts[:15]:
        print("-", t)

except Exception as e:
    print("Error:", e)
