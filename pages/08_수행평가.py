
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from pathlib import Path

# 1. 기본 설정
st.set_page_config(
    page_title="대한민국 범죄 현황 분석",
    page_icon="🔎",
    layout="wide"
)

st.title("🇰🇷 대한민국 범죄 현황 분석")
st.write("전국 시·군·구별 범죄 발생 현황을 분석합니다.")

# CSV 파일 경로
DATA_PATH = Path(__file__).parent / "crime.csv"

# 2. 전국 광역지역 중심 좌표
REGION_COORDS = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "세종": (36.4800, 127.2890),
    "경기도": (37.4138, 127.5183),
    "강원도": (37.8228, 128.1555),
    "충북": (36.6357, 127.4914),
    "충남": (36.6588, 126.6728),
    "전북": (35.7175, 127.1530),
    "전남": (34.8679, 126.9910),
    "경북": (36.4919, 128.8889),
    "경남": (35.4606, 128.2132),
    "제주": (33.4996, 126.5312)
}

# 3. 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, encoding="cp949")

    required = ["범죄대분류", "범죄중분류"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"{col} 열이 없습니다.")

    # 외국 지역 제외
    region_columns = [
        col for col in df.columns
        if col not in required
        and not str(col).startswith("외국 ")
    ]

    for col in region_columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0)

    return df, region_columns


if not DATA_PATH.exists():
    st.error(
        "crime(1).csv 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 넣어주세요."
    )
    st.stop()

try:
    data, region_columns = load_data()
except Exception as error:
    st.error(f"데이터 오류: {error}")
    st.stop()


# 4. 지역 선택
st.subheader("📍 분석할 지역 선택")

selected_region = st.selectbox(
    "전국 시·군·구 중 분석할 지역을 선택하세요.",
    region_columns
)

district_data = data[
    ["범죄대분류", "범죄중분류", selected_region]
].copy()

district_data = district_data.rename(
    columns={selected_region: "발생 건수"}
)

district_data["발생 건수"] = pd.to_numeric(
    district_data["발생 건수"],
    errors="coerce"
).fillna(0)

district_data = district_data[
    district_data["발생 건수"] > 0
]


# 5. 범죄 통계 계산
total_crime = int(district_data["발생 건수"].sum())

major_data = (
    district_data.groupby("범죄대분류")["발생 건수"]
    .sum()
    .sort_values(ascending=False)
)

minor_data = (
    district_data.groupby(
        ["범죄대분류", "범죄중분류"],
        as_index=False
    )["발생 건수"]
    .sum()
    .sort_values("발생 건수", ascending=False)
)

st.subheader(f"📊 {selected_region} 범죄 현황")

col1, col2, col3 = st.columns(3)

col1.metric("전체 범죄 발생 건수", f"{total_crime:,}건")
col2.metric("범죄 대분류 수", f"{len(major_data)}종")
col3.metric("세부 범죄 유형 수", f"{len(minor_data)}종")


# 6. 대한민국 지도
st.subheader("🗺️ 선택 지역 위치")

if selected_region == "세종시":
    selected_province = "세종"
else:
    selected_province = selected_region.split(" ")[0]

crime_map = folium.Map(
    location=(36.3, 127.8),
    zoom_start=7,
    tiles="CartoDB positron"
)

for province, coordinates in REGION_COORDS.items():

    selected = province == selected_province

    folium.CircleMarker(
        location=coordinates,
        radius=11 if selected else 6,
        color="red" if selected else "blue",
        fill=True,
        fill_color="red" if selected else "blue",
        fill_opacity=0.9,
        tooltip=province
    ).add_to(crime_map)

if selected_province in REGION_COORDS:

    folium.Marker(
        location=REGION_COORDS[selected_province],
        tooltip=f"선택 지역: {selected_region}",
        popup=f"분석 지역: {selected_region}",
        icon=folium.Icon(
            color="red",
            icon="info-sign"
        )
    ).add_to(crime_map)

st_folium(
    crime_map,
    use_container_width=True,
    height=500,
    returned_objects=[]
)

st.caption(
    "지도 마커는 광역자치단체의 대략적인 중심 위치입니다. "
    "개별 시·군·구의 정확한 행정구역 경계는 표시하지 않습니다."
)


# 7. 범죄 대분류별 그래프
st.subheader("📈 범죄 대분류별 발생 건수")

if not major_data.empty:

    major_df = major_data.reset_index()
    major_df.columns = ["범죄 유형", "발생 건수"]

    fig_major = px.bar(
        major_df.sort_values("발생 건수"),
        x="발생 건수",
        y="범죄 유형",
        orientation="h",
        text="발생 건수",
        color="발생 건수",
        color_continuous_scale="Blues",
        title=f"{selected_region} 범죄 유형별 발생 건수"
    )

    fig_major.update_layout(
        coloraxis_showscale=False,
        height=500,
        yaxis_title=""
    )

    st.plotly_chart(
        fig_major,
        use_container_width=True
    )

else:
    st.info("범죄 데이터가 없습니다.")


# 8. 세부 범죄 유형 분석
st.subheader("🔍 세부 범죄 유형 분석")

filtered_data = minor_data.copy()

if not major_data.empty:

    category_list = major_data.index.tolist()

    selected_categories = st.multiselect(
        "확인할 범죄 대분류를 선택하세요.",
        options=category_list,
        default=category_list
    )

    filtered_data = minor_data[
        minor_data["범죄대분류"].isin(selected_categories)
    ]

    if not filtered_data.empty:

        fig_minor = px.bar(
            filtered_data.sort_values("발생 건수"),
            x="발생 건수",
            y="범죄중분류",
            color="범죄대분류",
            orientation="h",
            title="세부 범죄 유형별 발생 건수",
            labels={
                "범죄중분류": "세부 범죄 유형",
                "발생 건수": "발생 건수",
                "범죄대분류": "범죄 대분류"
            }
        )

        fig_minor.update_layout(
            height=max(450, min(1000, len(filtered_data) * 30)),
            yaxis_title=""
        )

        st.plotly_chart(
            fig_minor,
            use_container_width=True
        )

        st.dataframe(
            filtered_data.rename(columns={
                "범죄대분류": "범죄 대분류",
                "범죄중분류": "범죄 중분류"
            }),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("선택한 범죄 유형의 데이터가 없습니다.")


# 9. 전국 지역별 범죄 발생 순위
st.subheader("🏆 전국 지역별 범죄 발생 순위")

national_totals = (
    data[region_columns]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

national_totals.columns = [
    "지역",
    "범죄 발생 건수"
]

top_regions = national_totals.head(15)

fig_rank = px.bar(
    top_regions.sort_values("범죄 발생 건수"),
    x="범죄 발생 건수",
    y="지역",
    orientation="h",
    text="범죄 발생 건수",
    color="범죄 발생 건수",
    color_continuous_scale="Oranges",
    title="범죄 발생 건수 상위 15개 지역"
)

fig_rank.update_layout(
    height=600,
    coloraxis_showscale=False,
    yaxis_title=""
)

st.plotly_chart(
    fig_rank,
    use_container_width=True
)


# 10. 분석 결과 다운로드
st.subheader("📥 분석 결과 다운로드")

csv_data = filtered_data.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="선택 지역 분석 결과 CSV 다운로드",
    data=csv_data,
    file_name="crime_analysis_result.csv",
    mime="text/csv"
)

st.divider()

st.caption(
    "본 분석은 사용자가 제공한 crime(1).csv 자료를 기반으로 합니다. "
    "범죄 발생 건수는 인구 규모를 보정한 범죄율이 아닙니다."
)
