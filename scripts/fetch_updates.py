#!/usr/bin/env python3
"""Fetch public RSS feeds for the homepage; standard library only."""
import datetime
import email.utils
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (compatible; orioninsist-feed/1.0)"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=18) as response:
        return response.read()

def feed(url, youtube=False):
    root = ET.fromstring(get(url))
    items = []
    if root.tag.endswith("rss"):
        for node in root.findall("./channel/item")[:2]:
            def val(name):
                element = node.find(name)
                return (element.text or "").strip() if element is not None else ""
            title, link, date = val("title"), val("link"), val("pubDate")
            try:
                date = email.utils.parsedate_to_datetime(date).strftime("%d %b %Y")
            except (ValueError, TypeError):
                date = ""
            if title and link.startswith("https://"):
                items.append({"title": title, "url": link, "date": date})
    else:
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        for node in root.findall("a:entry", ns)[:2]:
            title = node.findtext("a:title", "", ns)
            link_node = node.find("a:link", ns)
            link = link_node.get("href", "") if link_node is not None else ""
            date = node.findtext("a:published", "", ns)[:10]
            video_id = node.findtext("yt:videoId", "", ns)
            if title and link.startswith("https://"):
                item = {"title": title, "url": link, "date": date}
                if youtube and video_id:
                    item["image"] = "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg"
                items.append(item)
    return items

def first_available(urls):
    for url in urls:
        try:
            result = feed(url)
            if result:
                print("Loaded:", url)
                return result
        except Exception as exc:
            print("Feed unavailable:", url, str(exc)[:120])
    return []

def youtube_feed():
    try:
        page = get("https://www.youtube.com/@lilywithmilo").decode("utf-8", "ignore")
        match = re.search(r'"(?:channelId|externalId)"\s*:\s*"(UC[\w-]{22})"', page)
        if not match:
            match = re.search(r'channel/(UC[\w-]{22})', page)
        if match:
            return feed("https://www.youtube.com/feeds/videos.xml?channel_id=" + match.group(1), youtube=True)
    except Exception as exc:
        print("YouTube feed unavailable:", str(exc)[:160])
    return []

output = {
    "blog": first_available(["https://orioninsist.org/index.xml", "https://orioninsist.org/feed/", "https://orioninsist.org/feed.xml"]),
    "medium": first_available(["https://medium.com/feed/@orioninsist"]),
    "youtube": youtube_feed(),
}
path = pathlib.Path("data/updates.json")
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Feed counts:", {k: len(v) for k, v in output.items()})
