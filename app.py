import json
import os
from urllib.parse import quote_plus
import folium
import streamlit as st
from streamlit_folium import st_folium

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="世界のレストラン探索",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Load custom CSS
# ─────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
with open(css_path, "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Load restaurant data from JSON
# ─────────────────────────────────────────────
data_path = os.path.join(os.path.dirname(__file__), "data", "restaurants.json")
with open(data_path, "r", encoding="utf-8") as f:
    ALL_RESTAURANTS = json.load(f)

# ─────────────────────────────────────────────
# Area centers
# ─────────────────────────────────────────────
AREA_CENTERS = {
    "関東（東京）": (35.6812, 139.7671),
    "関西（大阪）": (34.7024, 135.4959),
}

# ─────────────────────────────────────────────
# Tag → CSS class
# ─────────────────────────────────────────────
TAG_CLASS_MAP = {
    "大使館職員御用達": "tag-embassy",
    "大阪関西万博出店": "tag-expo",
    "アフター万博": "tag-expo",
    "ハラール対応": "tag-halal",
    "ベジタリアンメニューあり": "tag-vege",
    "予約必須": "tag-reserve",
    "家族経営": "tag-family",
    "ワインセレクションあり": "tag-wine",
    "クラフトビール専門": "tag-beer",
    "テラス席あり": "tag-terrace",
    "テイクアウト可": "tag-takeout",
}

def tag_class(t):
    return TAG_CLASS_MAP.get(t, "tag-default")

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
if "area" not in st.session_state:
    st.session_state["area"] = "関東（東京）"

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
_num_cuisines = len(set(r['country'] for r in ALL_RESTAURANTS))
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
.hero-title {
  font-family: 'Cormorant Garamond', 'Noto Sans JP', serif;
  font-size: 2.6rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  background: linear-gradient(270deg, #c084fc, #818cf8, #60a5fa, #a78bfa, #c084fc);
  background-size: 300% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 6s linear infinite;
  margin: 0 0 2px 0;
  line-height: 1.2;
}
.hero-sub {
  color: #4b5563;
  font-size: 0.82rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin: 0 0 14px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.hero-sub span.dot { color: #6d28d9; font-size: 0.6rem; }
.hero-ornament {
  height: 1px;
  background: linear-gradient(90deg, transparent, #7c3aed 30%, #4f46e5 60%, transparent);
  box-shadow: 0 0 8px rgba(124,58,237,0.5);
  margin-bottom: 6px;
}
</style>
<div style="padding: 12px 0 8px 0;">
  <h1 class="hero-title">世界のレストランを、探索しよう。</h1>
  <p class="hero-sub">
    <span>Discover Authentic World Cuisine in Japan</span>
    <span class="dot">◆</span>
    <span>関東 &amp; 関西</span>
    <span class="dot">◆</span>
    <span>__NC__ Cuisines</span>
  </p>
  <div class="hero-ornament"></div>
</div>
""".replace("__NC__", str(_num_cuisines)), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Area Toggle
# ─────────────────────────────────────────────
selected_area = st.radio(
    "📍 エリアを選択",
    list(AREA_CENTERS.keys()),
    horizontal=True,
)
st.session_state["area"] = selected_area

area_key = "関東" if "関東" in selected_area else "関西"
area_restaurants = [r for r in ALL_RESTAURANTS if r["area"] == area_key]


# ─────────────────────────────────────────────
# Sidebar filters
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 絞り込み検索")
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    all_regions = sorted(set(r["region"] for r in area_restaurants))
    selected_regions = st.multiselect("🗺 地域・文化圏", options=all_regions, placeholder="すべての地域")

    if selected_regions:
        country_pool = [r for r in area_restaurants if r["region"] in selected_regions]
    else:
        country_pool = area_restaurants
    all_countries = sorted(set(r["country"] for r in country_pool))
    selected_countries = st.multiselect("🏳 国名", options=all_countries, placeholder="すべての国")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    all_tags = sorted(set(tag for r in area_restaurants for tag in r["tags"]))
    selected_tags = st.multiselect("🏷 特徴タグ", options=all_tags, placeholder="すべてのタグ")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    if st.button("🔄 フィルターをリセット", use_container_width=True):
        st.rerun()

# ─────────────────────────────────────────────
# Apply filters
# ─────────────────────────────────────────────
filtered = area_restaurants
if selected_regions:
    filtered = [r for r in filtered if r["region"] in selected_regions]
if selected_countries:
    filtered = [r for r in filtered if r["country"] in selected_countries]
if selected_tags:
    filtered = [r for r in filtered if any(t in r["tags"] for t in selected_tags)]

# ─────────────────────────────────────────────
# Layout: Map (left) | Cards (right)
# ─────────────────────────────────────────────
map_col, card_col = st.columns([1, 1], gap="large")

# ─────────────────────────────────────────────
# Folium Map
# ─────────────────────────────────────────────
with map_col:
    # 常にエリア中心で表示
    center = AREA_CENTERS[selected_area]

    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    for r in filtered:
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:160px;">
          <b style="font-size:14px;">{r['name']}</b><br>
          <span style="color:#888;font-size:12px;">{r['country']} / {r['region']}</span><br>
          <span style="font-size:12px;">🚃 {r['nearest_station']} 徒歩{r['walk_minutes']}分</span>
        </div>
        """
        folium.CircleMarker(
            location=[r["lat"], r["lng"]],
            radius=10,
            color="#a78bfa",
            fill=True,
            fill_color="#7c3aed",
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=r["name"],
        ).add_to(m)

    st_folium(m, height=560, use_container_width=True)


# ─────────────────────────────────────────────
# Restaurant Cards
# ─────────────────────────────────────────────
with card_col:
    count = len(filtered)
    st.markdown(
        f"<p class='results-count'>🍽 {count} 件のレストランが見つかりました</p>",
        unsafe_allow_html=True,
    )

    if count == 0:
        st.markdown(
            "<div class='no-results'>😔 条件に合うレストランが見つかりませんでした。<br>フィルターを変えてお試しください。</div>",
            unsafe_allow_html=True,
        )
    else:
        c1, c2 = st.columns(2, gap="medium")

        def render_card(r):
            tags_html = "".join(
                f"<span class='tag {tag_class(t)}'>{t}</span>"
                for t in r["tags"]
            )
            # Google Maps URLの生成（店名 + 住所で検索）
            query = quote_plus(f"{r['name']} {r.get('address', r['nearest_station'] + '駅')}")
            maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"
            return f"""
            <div class="restaurant-card">
              <img class="card-image" src="{r['image_url']}" alt="{r['name']}" loading="lazy" />
              <div class="card-body">
                <p class="card-title">{r['name']}</p>
                <span class="country-badge">🏳 {r['country']}</span>
                <span class="region-badge">{r['region']}</span>
                <div class="station-info">
                  <span>🚃</span>
                  <span>{r['nearest_station']}駅 &nbsp;徒歩 <strong style="color:#e2e8f0;">{r['walk_minutes']}分</strong></span>
                </div>
                <p class="description">{r['description']}</p>
                <div class="tags-container">{tags_html}</div>
                <a href="{maps_url}" target="_blank" rel="noopener noreferrer" class="maps-btn">
                  🗺️ Googleマップで見る
                </a>
              </div>
            </div>
            """

        left = filtered[::2]
        right = filtered[1::2]

        with c1:
            for r in left:
                st.markdown(render_card(r), unsafe_allow_html=True)
        with c2:
            for r in right:
                st.markdown(render_card(r), unsafe_allow_html=True)
