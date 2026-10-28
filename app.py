import re, requests, streamlit as st

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

if st.button("찾기"):
    try:
        h = re.search(r"@[^/?#\s]+", url).group()
        up = api("channels", part="contentDetails", forHandle=h)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
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
