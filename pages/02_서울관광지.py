
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울 인기 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

# 관광지 데이터
spots = [
    {
        "name": "명동",
        "english": "Myeong-dong",
        "lat": 37.5636, "lon": 126.9850,
        "category": "쇼핑 · 먹거리",
        "description": "화장품 매장과 패션 상점, 길거리 음식이 모여 있는 서울 대표 쇼핑 거리입니다. 다양한 한국 간식과 최신 유행을 경험할 수 있습니다."
    },
    {
        "name": "N서울타워",
        "english": "N Seoul Tower",
        "lat": 37.5512, "lon": 126.9882,
        "category": "전망 · 랜드마크",
        "description": "남산 정상 부근에 있는 서울의 대표 랜드마크입니다. 전망대와 주변 산책로에서 서울 도심의 풍경을 감상할 수 있습니다."
    },
    {
        "name": "코엑스",
        "english": "COEX",
        "lat": 37.5116, "lon": 127.0592,
        "category": "쇼핑 · 문화",
        "description": "대형 전시장과 쇼핑몰, 아쿠아리움 등이 모여 있는 복합 문화 공간입니다. 별마당도서관의 높은 서가도 인기 사진 명소입니다."
    },
    {
        "name": "강남역 일대",
        "english": "Gangnam Station Area",
        "lat": 37.4979, "lon": 127.0276,
        "category": "쇼핑 · 도시문화",
        "description": "패션 매장과 음식점, 카페가 밀집한 번화가입니다. 현대적인 서울의 분위기와 활기찬 거리를 느낄 수 있습니다."
    },
    {
        "name": "홍대 거리",
        "english": "Hongdae",
        "lat": 37.5563, "lon": 126.9236,
        "category": "공연 · 청년문화",
        "description": "버스킹과 공연, 개성 있는 상점과 카페로 유명한 거리입니다. 한국의 대중문화와 젊은 예술 분위기를 즐기기 좋습니다."
    },
    {
        "name": "경복궁",
        "english": "Gyeongbokgung Palace",
        "lat": 37.5796, "lon": 126.9770,
        "category": "역사 · 전통문화",
        "description": "조선 왕조의 법궁으로, 웅장한 건축물과 아름다운 궁궐 정원을 볼 수 있습니다. 한복을 입고 방문하는 관광객도 많습니다."
    },
    {
        "name": "북촌한옥마을",
        "english": "Bukchon Hanok Village",
        "lat": 37.5826, "lon": 126.9830,
        "category": "전통 · 골목길",
        "description": "전통 한옥이 모여 있는 마을로, 서울의 옛 주거 문화를 느낄 수 있습니다. 실제 주민이 거주하는 곳이므로 조용히 관람해야 합니다."
    },
    {
        "name": "동대문디자인플라자(DDP)",
        "english": "Dongdaemun Design Plaza",
        "lat": 37.5671, "lon": 127.0095,
        "category": "건축 · 디자인",
        "description": "곡선형 외관이 인상적인 복합 문화 공간입니다. 전시와 디자인 행사, 야간 조명으로 잘 알려져 있습니다."
    },
    {
        "name": "광장시장",
        "english": "Gwangjang Market",
        "lat": 37.5700, "lon": 126.9997,
        "category": "전통시장 · 음식",
        "description": "빈대떡과 김밥 등 다양한 한국 시장 음식을 맛볼 수 있는 전통시장입니다. 활기찬 시장 분위기를 경험할 수 있습니다."
    },
    {
        "name": "성수동·서울숲",
        "english": "Seongsu-dong & Seoul Forest",
        "lat": 37.5445, "lon": 127.0560,
        "category": "카페 · 자연",
        "description": "개성 있는 카페와 편집숍, 팝업스토어가 많은 성수동과 도심 속 휴식 공간인 서울숲을 함께 둘러볼 수 있습니다."
    }
]

# 1일 차 일정
day1 = [
    {"시간": "09:00–10:30", "일정": "홍대 거리", "내용": "거리 구경, 개성 있는 상점과 카페 방문"},
    {"시간": "10:30–11:15", "일정": "이동", "내용": "홍대에서 경복궁으로 이동"},
    {"시간": "11:15–12:30", "일정": "경복궁", "내용": "근정전과 경회루 등 궁궐 관람"},
    {"시간": "12:30–13:30", "일정": "점심 식사", "내용": "경복궁 주변에서 한식 식사"},
    {"시간": "13:30–15:00", "일정": "북촌한옥마을", "내용": "한옥 골목 산책과 전통 경관 감상"},
    {"시간": "15:00–15:40", "일정": "이동", "내용": "북촌에서 광장시장으로 이동"},
    {"시간": "15:40–17:00", "일정": "광장시장", "내용": "빈대떡, 김밥 등 전통시장 먹거리 체험"},
    {"시간": "17:00–17:20", "일정": "이동", "내용": "광장시장에서 DDP로 이동"},
    {"시간": "17:20–18:40", "일정": "동대문디자인플라자(DDP)", "내용": "건축물 감상 및 전시 공간 둘러보기"},
    {"시간": "18:40–20:00", "일정": "저녁 및 휴식", "내용": "동대문 일대에서 저녁 식사 후 숙소로 이동"}
]

# 2일 차 일정
day2 = [
    {"시간": "09:00–10:30", "일정": "명동", "내용": "쇼핑 거리 산책과 상점 구경"},
    {"시간": "10:30–11:00", "일정": "이동", "내용": "명동에서 남산 케이블카 승강장 방향으로 이동"},
    {"시간": "11:00–13:00", "일정": "N서울타워", "내용": "남산 산책, 전망 감상 및 점심 식사"},
    {"시간": "13:00–13:50", "일정": "이동", "내용": "남산에서 강남역으로 이동"},
    {"시간": "13:50–15:00", "일정": "강남역 일대", "내용": "강남 거리와 상점, 카페 둘러보기"},
    {"시간": "15:00–15:20", "일정": "이동", "내용": "강남역에서 코엑스로 이동"},
    {"시간": "15:20–17:00", "일정": "코엑스", "내용": "별마당도서관과 쇼핑몰 관람"},
    {"시간": "17:00–17:30", "일정": "이동", "내용": "코엑스에서 성수동·서울숲으로 이동"},
    {"시간": "17:30–19:00", "일정": "성수동·서울숲", "내용": "카페와 편집숍 구경, 서울숲 산책"},
    {"시간": "19:00–20:00", "일정": "저녁 및 마무리", "내용": "성수동에서 저녁 식사 후 일정 종료"}
]

# 제목
st.title("🗺️ 외국인 관광객이 사랑하는 서울 인기 관광지 TOP 10")

st.caption(
    "서울의 대표 관광 명소를 지도에서 확인하고, "
    "각 장소의 특징과 1박 2일 여행 일정을 살펴보세요."
)

st.info(
    "관광지 10곳은 서울의 대표 관광 명소를 참고해 구성한 안내 목록이며, "
    "공식적인 외국인 방문 순위 1~10위는 아닙니다."
)

# 서울 지도 생성
m = folium.Map(
    location=[37.5665, 126.9780],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)

# 지도에 관광지 표시
for idx, spot in enumerate(spots, start=1):

    popup_html = f"""
    <div style="width:230px; font-family:sans-serif;">
        <b style="font-size:15px;">
            {idx}. {spot['name']}
        </b>
        <br>
        <span style="color:#666;">
            {spot['english']}
        </span>
        <br>
        <b>{spot['category']}</b>
        <p>{spot['description']}</p>
    </div>
    """

    folium.Marker(
        location=[spot["lat"], spot["lon"]],
        tooltip=f"{idx}. {spot['name']}",
        popup=folium.Popup(
            popup_html,
            max_width=280
        ),
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background:#2563eb;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:30px;
                height:30px;
                line-height:26px;
                text-align:center;
                font-weight:bold;
                box-shadow:0 1px 5px #555;
            ">
                {idx}
            </div>
            """,
            icon_size=(30, 30),
            icon_anchor=(15, 15)
        )
    ).add_to(m)

# 지도 출력
st.subheader("📍 서울 관광지 위치")

st_folium(
    m,
    width=None,
    height=570,
    returned_objects=[],
    use_container_width=True
)

# ==================================
# 추가 기능 : 1박 2일 여행 일정표
# ==================================

st.divider()

st.subheader("🧳 서울 주요 관광지 1박 2일 여행 코스")

st.write(
    "매일 오전 9시부터 오후 8시까지 운영되는 일정 예시입니다. "
    "관광지 관람뿐 아니라 식사와 장소 간 이동 시간도 포함했습니다."
)

# 날짜별 탭
tab1, tab2 = st.tabs([
    "DAY 1 · 서울 서쪽과 도심",
    "DAY 2 · 남산과 강남·성수"
])

# 첫째 날
with tab1:

    st.markdown("#### 첫째 날 — 홍대에서 동대문까지")

    st.table(day1)

# 둘째 날
with tab2:

    st.markdown("#### 둘째 날 — 명동에서 성수까지")

    st.table(day2)

st.caption(
    "※ 이동 시간은 교통 상황과 출발 위치에 따라 달라질 수 있습니다. "
    "실제 방문 전 대중교통 경로와 관광지 운영 시간을 확인하세요. "
    "경복궁 등 일부 관광지는 휴궁일이나 운영 시간에 유의해야 합니다."
)

# ==================================
# 관광지 소개
# ==================================

st.divider()

st.subheader("🏙️ 관광지 TOP 10 소개")

st.write(
    "각 관광지의 이름과 특징을 간단하게 정리했습니다."
)

# 관광지 2개씩 표시
for start in range(0, len(spots), 2):

    cols = st.columns(2)

    for col, (idx, spot) in zip(
        cols,
        enumerate(spots[start:start + 2], start=start + 1)
    ):

        with col:

            st.markdown(
                f"### {idx}. {spot['name']}"
            )

            st.caption(
                f"{spot['english']} · {spot['category']}"
            )

            st.write(spot["description"])

            st.markdown(
                f"[📍 Google 지도에서 위치 보기]"
                f"(https://www.google.com/maps/search/?api=1&query={spot['lat']},{spot['lon']})"
            )

    st.write("")

# 하단 안내
st.divider()

st.caption(
    "서울의 대표 관광 명소를 소개하는 지도 서비스입니다. "
    "관광지 좌표는 지도 표시를 위한 대표 위치입니다."
)
