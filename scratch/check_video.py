import urllib.request
import re
import json

url = "https://www.youtube.com/watch?v=OjB6SBK_aDc"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")

    title_match = re.search(r"<title>(.*?)</title>", html)
    print("TITLE:", title_match.group(1) if title_match else "None")

    # Search for ytInitialPlayerResponse
    player_match = re.search(r"ytInitialPlayerResponse\s*=\s*({.+?});", html)
    if player_match:
        data = json.loads(player_match.group(1))
        details = data.get("videoDetails", {})
        print("VIDEO DETAILS:")
        print("Title:", details.get("title"))
        print("Author:", details.get("author"))
        print("Channel ID:", details.get("channelId"))
        print("Length Seconds:", details.get("lengthSeconds"))
        print("Keywords:", details.get("keywords"))
        print("Short Description:", details.get("shortDescription"))
        print("Is Live:", details.get("isLiveContent"))
    else:
        print("No ytInitialPlayerResponse match")
        desc_match = re.search(r'"shortDescription":"(.*?)"', html)
        if desc_match:
            print("Description:", desc_match.group(1))

except Exception as e:
    print("Error:", e)
