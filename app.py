import re, requests, streamlit as st
from urllib.parse import unquote

st.title("👍 채널 좋아요 TOP 5")
B = "https://www.googleapis.com/youtube/v3/"

if "YT_KEY" not in st.secrets:
    st.error("Secrets에 YT_KEY가 없어요.")
    st.stop()
key = st.secrets["YT_KEY"]

url = st.text_input("채널 주소 (예: https://www.youtube.com/@채널핸들)")

def api(p, **q):
    d = requests.get(B + p, params={**q, "key": key}).json()
    if "error" in d: raise Exception(d["error"]["message"])
    return d

def find_channel(u):
    u = unquote(u.strip())
    m = re.search(r"@[^/?#\s]+", u)
    if m: return {"forHandle": m.group()}
    m = re.search(r"channel/(UC[\w-]+)", u)
    if m: return {"id": m.group(1)}
    m = re.search(r"user/([^/?#\s]+)", u)
    if m: return {"forUsername": m.group(1)}
    m = re.search(r"/c/([^/?#\s]+)", u)
    if m:
        s = api("search", part="snippet", q=m.group(1), type="channel", maxResults=1)
        return {"id": s["items"][0]["snippet"]["channelId"]}
    raise Exception("채널 주소가 아니에요. 채널 페이지의 주소를 넣어주세요.")

if st.button("찾기"):
    try:
        ch = api("channels", part="snippet,contentDetails", **find_channel(url))
        if not ch.get("items"):
            raise Exception("채널을 찾지 못했어요.")
        st.subheader(ch["items"][0]["snippet"]["title"])
        up = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        ids, t = [], None
        while True:
            d = api("playlistItems", part="contentDetails", playlistId=up, maxResults=50, **({"pageToken": t} if t else {}))
            ids += [i["contentDetails"]["videoId"] for i in d["items"]]
            t = d.get("nextPageToken")
            if not t: break
        vs = []
        for i in range(0, len(ids), 50):
            for v in api("videos", part="snippet,statistics", id=",".join(ids[i:i+50]))["items"]:
                vs.append((int(v["statistics"].get("likeCount", 0)), v["snippet"]["title"], v["id"]))
        for n, (l, title, vid) in enumerate(sorted(vs, reverse=True)[:5], 1):
            st.write(f"**{n}위** 👍{l:,} | [{title}](https://youtu.be/{vid})")
    except Exception as e:
        st.error(f"오류: {e}")
