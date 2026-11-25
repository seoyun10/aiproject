
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from pathlib import Path

# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="대한민국 범죄 현황 분석",
    page_icon="🗺️",
    layout="wide"
)

st.title("🇰🇷 대한민국 범죄 현황 분석")
st.write("전국 지역별 범죄 발생 현황을 지도와 그래프로 분석합니다.")

# CSV 파일 경로
DATA_PATH = Path(__file__).parent / "crime.csv"


# ==========================================
# 2. 지역별 좌표
# ==========================================

REGION_COORDS = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "세종": (36.4800, 127.2890),
    "경기": (37.4138, 127.5183),
    "강원": (37.8228, 128.1555),
    "충북": (36.6357, 127.4914),
    "충남": (36.6588, 126.6728),
    "전북": (35.7175, 127.1530),
    "전남": (34.8679, 126.9910),
    "경북": (36.4919, 128.8889),
    "경남": (35.4606, 128.2132),
    "제주": (33.4996, 126.5312)
}

# 다양한 지역명 표기를 표준 시·도명으로 변환
REGION_ALIASES = {
    "서울": ["서울", "서울특별시"],
    "부산": ["부산", "부산광역시"],
    "대구": ["대구", "대구광역시"],
    "인천": ["인천", "인천광역시"],
    "광주": ["광주", "광주광역시"],
    "대전": ["대전", "대전광역시"],
    "울산": ["울산", "울산광역시"],
    "세종": ["세종", "세종시", "세종특별자치시"],
    "경기": ["경기", "경기도"],
    "강원": ["강원", "강원도", "강원특별자치도"],
    "충북": ["충북", "충청북도"],
    "충남": ["충남", "충청남도"],
    "전북": ["전북", "전라북도", "전북특별자치도"],
    "전남": ["전남", "전라남도"],
    "경북": ["경북", "경상북도"],
    "경남": ["경남", "경상남도"],
    "제주": ["제주", "제주도", "제주특별자치도"]
}


def get_province(column_name):
    name = str(column_name).strip()

    for province, aliases in REGION_ALIASES.items():
        for alias in aliases:
            if name == alias or name.startswith(alias + " "):
                return province

    return None


# ==========================================
# 3. 데이터 불러오기
# ==========================================

@st.cache_data
def load_data(file_path):

    df = None

    for encoding in ["cp949", "utf-8-sig", "utf-8"]:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 파일의 인코딩을 확인해주세요.")

    required = ["범죄대분류", "범죄중분류"]

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"CSV에 '{column}' 열이 없습니다."
            )

    region_columns = [
        col for col in df.columns
        if get_province(col) is not None
    ]

    if not region_columns:
        raise ValueError(
            "지역 열을 찾을 수 없습니다. CSV의 지역 열 이름을 확인해주세요."
        )

    for col in region_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    return df, region_columns


if not DATA_PATH.exists():
    st.error(
        "crime.csv 파일을 찾을 수 없습니다. "
        "app.py와 crime.csv가 같은 폴더에 있는지 확인해주세요."
    )
    st.stop()

try:
    data, region_columns = load_data(str(DATA_PATH))

except Exception as e:
    st.error(f"데이터 오류: {e}")
    st.stop()


# ==========================================
# 4. 지역 선택
# ==========================================

st.subheader("📍 분석 지역 선택")

selected_region = st.selectbox(
    "분석할 지역을 선택하세요.",
    region_columns
)

selected_province = get_province(selected_region)

selected_data = data[
    ["범죄대분류", "범죄중분류", selected_region]
].copy()

selected_data = selected_data.rename(
    columns={selected_region: "발생 건수"}
)

selected_data["발생 건수"] = pd.to_numeric(
    selected_data["발생 건수"],
    errors="coerce"
).fillna(0)

selected_data = selected_data[
    selected_data["발생 건수"] > 0
]


# ==========================================
# 5. 통계 계산
# ==========================================

total_crime = int(selected_data["발생 건수"].sum())

major_data = (
    selected_data.groupby("범죄대분류")["발생 건수"]
    .sum()
    .reset_index()
    .sort_values("발생 건수", ascending=False)
)

minor_data = (
    selected_data.groupby(
        ["범죄대분류", "범죄중분류"]
    )["발생 건수"]
    .sum()
    .reset_index()
    .sort_values("발생 건수", ascending=False)
)

col1, col2, col3 = st.columns(3)

col1.metric("전체 범죄 발생 건수", f"{total_crime:,}건")
col2.metric("범죄 대분류", f"{len(major_data)}종")
col3.metric("범죄 중분류", f"{len(minor_data)}종")


# ==========================================
# 6. 시·도별 범죄 건수 계산
# ==========================================

province_totals = {}

for province in REGION_COORDS:

    columns = [
        col for col in region_columns
        if get_province(col) == province
    ]

    if columns:
        province_totals[province] = int(
            data[columns].sum().sum()
        )


# ==========================================
# 7. OpenStreetMap 전국 지도
# ==========================================

st.subheader("🗺️ 대한민국 전국 범죄 현황 지도")

st.write(
    "지도에서 지역별 마커를 클릭하면 "
    "해당 지역의 범죄 발생 건수를 확인할 수 있습니다."
)

# OpenStreetMap을 배경으로 사용
crime_map = folium.Map(
    location=[36.3, 127.8],
    zoom_start=7,
    min_zoom=6,
    max_zoom=15,
    tiles="OpenStreetMap",
    control_scale=True
)

# 지도 표시 영역 설정
crime_map.fit_bounds([
    [33.0, 124.0],
    [39.0, 132.0]
])

# 마커 크기 계산
max_crime = max(province_totals.values()) if province_totals else 1

for province, coordinates in REGION_COORDS.items():

    if province not in province_totals:
        continue

    count = province_totals[province]

    # 선택한 시·도 강조
    is_selected = province == selected_province

    radius = 7 + (count / max_crime) * 13

    marker_color = "red" if is_selected else "blue"

    popup_html = f"""
    <div style="font-family:Arial; width:180px;">
        <h4>{province}</h4>
        <p>범죄 발생 건수</p>
        <h3>{count:,}건</h3>
        <p>선택 지역: {selected_region}</p>
    </div>
    """

    folium.CircleMarker(
        location=coordinates,
        radius=radius,
        color=marker_color,
        weight=2,
        fill=True,
        fill_color=marker_color,
        fill_opacity=0.65,
        tooltip=f"{province}: {count:,}건",
        popup=folium.Popup(
            popup_html,
            max_width=250
        )
    ).add_to(crime_map)

    # 지역명 표시
    folium.Marker(
        location=coordinates,
        icon=folium.DivIcon(
            html=f"""
            <div style="
                font-size:11px;
                font-weight:bold;
                color:#222;
                white-space:nowrap;
                text-shadow:1px 1px white;
            ">
                {province}
            </div>
            """
        )
    ).add_to(crime_map)


# 지도 화면 출력
st_folium(
    crime_map,
    width=None,
    height=600,
    use_container_width=True,
    returned_objects=[],
    key="korea_crime_map"
)

st.caption(
    "지도 출처: OpenStreetMap contributors. "
    "마커는 시·도별 범죄 발생 건수를 나타냅니다."
)


# ==========================================
# 8. 시·도별 범죄 통계
# ==========================================

st.subheader("📊 전국 시·도별 범죄 발생 건수")

if province_totals:

    province_df = pd.DataFrame(
        list(province_totals.items()),
        columns=["지역", "범죄 발생 건수"]
    ).sort_values(
        "범죄 발생 건수",
        ascending=False
    )

    fig_province = px.bar(
        province_df,
        x="지역",
        y="범죄 발생 건수",
        color="범죄 발생 건수",
        color_continuous_scale="Reds",
        text="범죄 발생 건수",
        title="전국 시·도별 범죄 발생 건수"
    )

    st.plotly_chart(
        fig_province,
        use_container_width=True
    )


# ==========================================
# 9. 범죄 대분류 분석
# ==========================================

st.subheader("📈 범죄 대분류별 발생 건수")

if not major_data.empty:

    fig_major = px.bar(
        major_data,
        x="범죄대분류",
        y="발생 건수",
        color="발생 건수",
        color_continuous_scale="Blues",
        text="발생 건수",
        title=f"{selected_region} 범죄 대분류 분석"
    )

    st.plotly_chart(
        fig_major,
        use_container_width=True
    )


# ==========================================
# 10. 범죄 중분류 분석
# ==========================================

st.subheader("🔎 세부 범죄 유형 분석")

if not major_data.empty:

    categories = major_data["범죄대분류"].tolist()

    selected_categories = st.multiselect(
        "분석할 범죄 대분류를 선택하세요.",
        categories,
        default=categories
    )

    filtered_data = minor_data[
        minor_data["범죄대분류"].isin(selected_categories)
    ]

    if not filtered_data.empty:

        fig_minor = px.bar(
            filtered_data,
            x="발생 건수",
            y="범죄중분류",
            color="범죄대분류",
            orientation="h",
            title=f"{selected_region} 세부 범죄 유형 분석"
        )

        st.plotly_chart(
            fig_minor,
            use_container_width=True
        )

        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("선택한 범죄 유형의 데이터가 없습니다.")


# ==========================================
# 11. 데이터 표
# ==========================================

with st.expander("원본 데이터 확인하기"):

    st.dataframe(
        data,
        use_container_width=True
    )

st.divider()

st.caption(
    "대한민국 범죄 현황 분석 프로젝트"
)
