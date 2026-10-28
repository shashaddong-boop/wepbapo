import re
import requests
import streamlit as st

st.set_page_config(page_title="유튜브 좋아요 TOP 5", page_icon="👍")

BASE = "https://www.googleapis.com/youtube/v3"
API_KEY = st.secrets["YT_KEY"]  # 키는 코드에 쓰지 않고 Secrets에 저장


def call_api(path, **params):
    params["key"] = API_KEY
    data = requests.get(f"{BASE}/{path}", params=params, timeout=15).json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "알 수 없는 오류"))
    return data


def parse_channel(text):
    text = text.strip()
    if text.startswith("@"):
        return "handle", text
    m = re.search(r"youtube\.com/(@[^/?#\s]+)", text)
    if m:
        return "handle", m.group(1)
    m = re.search(r"youtube\.com/channel/(UC[\w-]+)", text)
    if m:
        return "id", m.group(1)
    return None, None


@st.cache_data(ttl=3600, show_spinner=False)
def get_top_videos(kind, value, top_n=5):
    # 1. 채널 정보 + 업로드 목록 ID
    if kind == "handle":
        ch = call_api("channels", part="snippet,contentDetails", forHandle=value)
    else:
        ch = call_api("channels", part="snippet,contentDetails", id=value)
    if not ch.get("items"):
        return None, []

    channel = ch["items"][0]
    name = channel["snippet"]["title"]
    uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. 모든 영상 ID 가져오기
    video_ids = []
    params = {"part": "contentDetails", "playlistId": uploads_id, "maxResults": 50}
    for _ in range(40):
        data = call_api("playlistItems", **params)
        video_ids += [i["contentDetails"]["videoId"] for i in data["items"]]
        if "nextPageToken" not in data:
            break
        params["pageToken"] = data["nextPageToken"]

    # 3. 좋아요/조회수 가져오기 (50개씩)
    videos = []
    for i in range(0, len(video_ids), 50):
        data = call_api("videos", part="snippet,statistics",
                        id=",".join(video_ids[i:i + 50]))
        for v in data["items"]:
            s = v["statistics"]
            videos.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "thumbnail": v["snippet"]["thumbnails"]["medium"]["url"],
                "likes": int(s.get("likeCount", 0)),
                "views": int(s.get("viewCount", 0)),
            })

    videos.sort(key=lambda x: x["likes"], reverse=True)
    return name, videos[:top_n]


st.title("👍 채널 좋아요 TOP 5")
url = st.text_input("채널 주소", placeholder="https://www.youtube.com/@채널핸들")

if url.strip():
    kind, value = parse_channel(url)
    if not kind:
        st.error("주소 형식을 확인해 주세요. 예: https://www.youtube.com/@채널핸들")
    else:
        try:
            with st.spinner("가져오는 중..."):
                name, top = get_top_videos(kind, value)
        except Exception as e:
            st.error(f"오류: {e}")
        else:
            if not name:
                st.error("채널을 찾지 못했어요.")
            else:
                st.subheader(f"{name} 채널")
                for n, v in enumerate(top, 1):
                    c1, c2 = st.columns([1, 2])
                    c1.image(v["thumbnail"])
                    c2.markdown(f"**{n}위. {v['title']}**")
                    c2.write(f"👍 {v['likes']:,}개 · 👁️ {v['views']:,}회")
                    c2.link_button("영상 보기", f"https://youtu.be/{v['id']}")
                    st.divider()
