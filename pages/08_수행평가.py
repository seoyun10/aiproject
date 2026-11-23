
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from pathlib import Path

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="대한민국 범죄 현황 분석",
    page_icon="🔎",
    layout="wide"
)

st.title("🇰🇷 대한민국 범죄 현황 분석")
st.caption("전국 시·군·구별 범죄 발생 건수를 범죄 유형에 따라 분석합니다.")

# app.py와 crime.csv를 같은 폴더에 넣어주세요.
DATA_PATH = Path(__file__).parent / "crime.csv"

# --------------------------------------------------
# 2. 전국 광역자치단체 중심 좌표
# --------------------------------------------------
PROVINCE_COORDS = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "세종시": (36.4800, 127.2890),
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

PROVINCE_PREFIXES = [
    "경기도", "강원도", "서울", "부산", "대구", "인천",
    "광주", "대전", "울산", "세종시", "충북", "충남",
    "전북", "전남", "경북", "경남", "제주"
]


def get_province(region_name):
    """지역 열에서 광역자치단체 이름을 추출합니다."""
    region_name = str(region_name).strip()

    if region_name == "세종시":
        return "세종시"

    for prefix in PROVINCE_PREFIXES:
        if region_name == prefix or region_name.startswith(prefix + " "):
            return prefix

    return None


# --------------------------------------------------
# 3. CSV 파일 불러오기
# --------------------------------------------------
@st.cache_data
def load_data(file_path):

    data = None
    last_error = None

    for encoding in ["cp949", "utf-8-sig", "utf-8"]:
        try:
            data = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError as error:
            last_error = error

    if data is None:
        raise ValueError(
            f"CSV 인코딩을 확인할 수 없습니다: {last_error}"
        )

    required_columns = [
        "범죄대분류",
        "범죄중분류"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "CSV에 필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )

    # 외국 관련 열은 제외하고 국내 지역 열만 추출
    region_columns = []

    for col in data.columns:

        if col in required_columns:
            continue

        if str(col).startswith("외국 "):
            continue

        if get_province(col) is not None:
            region_columns.append(col)

    if not region_columns:
        raise ValueError(
            "CSV에서 국내 시·군·구 지역 열을 찾지 못했습니다."
        )

    for col in region_columns:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        ).fillna(0)

    return data, region_columns


if not DATA_PATH.exists():

    st.error(
        "crime.csv 파일을 찾을 수 없습니다.\n\n"
        "GitHub 저장소에서 app.py와 crime.csv가 "
        "같은 폴더에 있는지 확인하세요."
    )

    st.stop()


try:
    data, region_columns = load_data(str(DATA_PATH))

except Exception as error:

    st.error(
        f"데이터를 불러오는 중 오류가 발생했습니다: {error}"
    )

    st.stop()


# --------------------------------------------------
# 4. 분석 지역 선택
# --------------------------------------------------
st.subheader("📍 분석할 지역 선택")

selected_region = st.selectbox(
    "전국 시·군·구 중 분석할 지역을 선택하세요.",
    options=region_columns
)

selected_province = get_province(selected_region)

# 선택한 지역의 범죄 자료
selected_data = data[
    ["범죄대분류", "범죄중분류", selected_region]
].copy()

selected_data = selected_data.rename(
    columns={
        selected_region: "발생 건수"
    }
)

selected_data["발생 건수"] = pd.to_numeric(
    selected_data["발생 건수"],
    errors="coerce"
).fillna(0)

selected_data = selected_data[
    selected_data["발생 건수"] > 0
]


# --------------------------------------------------
# 5. 선택 지역 통계
# --------------------------------------------------
total_crime = int(
    selected_data["발생 건수"].sum()
)

major_data = (
    selected_data.groupby(
        "범죄대분류",
        as_index=False
    )["발생 건수"]
    .sum()
    .sort_values(
        "발생 건수",
        ascending=False
    )
)

minor_data = (
    selected_data.groupby(
        ["범죄대분류", "범죄중분류"],
        as_index=False
    )["발생 건수"]
    .sum()
    .sort_values(
        "발생 건수",
        ascending=False
    )
)

st.subheader(
    f"📊 {selected_region} 범죄 현황"
)

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "전체 범죄 발생 건수",
    f"{total_crime:,}건"
)

metric2.metric(
    "범죄 대분류 수",
    f"{len(major_data)}종"
)

metric3.metric(
    "세부 범죄 유형 수",
    f"{len(minor_data)}종"
)


# --------------------------------------------------
# 6. 대한민국 전국 범죄 현황 지도
# --------------------------------------------------
st.subheader("🗺️ 대한민국 전국 범죄 현황 지도")

st.write(
    "지도에서 시·도별 마커를 누르면 "
    "해당 지역의 범죄 발생 건수를 확인할 수 있습니다."
)

# 시·도별 범죄 발생 건수 합산
province_totals = {}

for province in PROVINCE_COORDS:

    province_cols = [
        col for col in region_columns
        if get_province(col) == province
    ]

    if province_cols:

        province_totals[province] = int(
            data[province_cols]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .to_numpy()
            .sum()
        )


# 전국 지도 생성
crime_map = folium.Map(
    location=[36.3, 127.8],
    zoom_start=7,
    tiles="CartoDB positron",
    control_scale=True
)

max_total = (
    max(province_totals.values())
    if province_totals
    else 1
)


# 시·도별 마커 표시
for province, coordinates in PROVINCE_COORDS.items():

    if province not in province_totals:
        continue

    count = province_totals[province]

    is_selected = province == selected_province

    marker_radius = 7 + (count / max_total) * 13

    popup_html = f"""
    <div style='font-family: sans-serif; min-width: 150px;'>
        <b>{province}</b><br>
        전체 범죄 발생 건수:
        <b>{count:,}건</b><br>
        {'선택한 지역이 포함된 시·도' if is_selected else ''}
    </div>
    """

    folium.CircleMarker(
        location=coordinates,
        radius=marker_radius,
        color="#d62728" if is_selected else "#2878b5",
        weight=3 if is_selected else 1.5,
        fill=True,
        fill_color="#ff4d4d" if is_selected else "#5b9bd5",
        fill_opacity=0.85,
        tooltip=f"{province}: {count:,}건",
        popup=folium.Popup(
            popup_html,
            max_width=250
        )
    ).add_to(crime_map)

    # 지도 위에 지역 이름 표시
    folium.Marker(
        location=coordinates,
        tooltip=f"{province} {count:,}건",
        icon=folium.DivIcon(
            html=(
                "<div style='font-size:10px; font-weight:bold; "
                "color:#202020; white-space:nowrap;'>"
                f"{province}</div>"
            )
        )
    ).add_to(crime_map)


# Streamlit 화면에 지도 출력
st_folium(
    crime_map,
    use_container_width=True,
    height=560,
    returned_objects=[],
    key="national_crime_map"
)

st.caption(
    "※ 지도는 시·도별 중심 좌표에 마커를 표시합니다. "
    "마커의 범죄 건수는 해당 시·도에 속한 CSV 지역 열의 합계이며, "
    "시·군·구 경계선을 표시하는 지도는 아닙니다."
)


# --------------------------------------------------
# 7. 시·도별 범죄 발생 건수 표
# --------------------------------------------------
if province_totals:

    province_summary = pd.DataFrame(
        list(province_totals.items()),
        columns=[
            "시·도",
            "범죄 발생 건수"
        ]
    ).sort_values(
        "범죄 발생 건수",
        ascending=False
    )

    with st.expander(
        "시·도별 범죄 발생 건수 표 보기"
    ):

        st.dataframe(
            province_summary,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# 8. 범죄 대분류별 분석
# --------------------------------------------------
st.subheader("📈 범죄 대분류별 발생 건수")

if not major_data.empty:

    fig_major = px.bar(
        major_data.sort_values(
            "발생 건수",
            ascending=True
        ),
        x="발생 건수",
        y="범죄대분류",
        orientation="h",
        text="발생 건수",
        color="발생 건수",
        color_continuous_scale="Blues",
        labels={
            "범죄대분류": "범죄 유형",
            "발생 건수": "발생 건수"
        },
        title=f"{selected_region} 범죄 대분류별 발생 건수"
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

    st.info(
        "선택한 지역에 표시할 범죄 데이터가 없습니다."
    )


# --------------------------------------------------
# 9. 범죄 중분류별 상세 분석
# --------------------------------------------------
st.subheader("🔍 세부 범죄 유형 분석")

if not major_data.empty:

    category_list = major_data[
        "범죄대분류"
    ].tolist()

    selected_categories = st.multiselect(
        "확인할 범죄 대분류를 선택하세요.",
        options=category_list,
        default=category_list
    )

    filtered_data = minor_data[
        minor_data["범죄대분류"].isin(
            selected_categories
        )
    ]

    if not filtered_data.empty:

        fig_minor = px.bar(
            filtered_data.sort_values(
                "발생 건수",
                ascending=True
            ),
            x="발생 건수",
            y="범죄중분류",
            color="범죄대분류",
            orientation="h",
            title=f"{selected_region} 세부 범죄 유형별 발생 건수",
            labels={
                "범죄중분류": "세부 범죄 유형",
                "발생 건수": "발생 건수",
                "범죄대분류": "범죄 대분류"
            }
        )

        fig_minor.update_layout(
            height=max(
                450,
                min(1000, len(filtered_data) * 30)
            ),
            yaxis_title=""
        )

        st.plotly_chart(
            fig_minor,
            use_container_width=True
        )

        st.dataframe(
            filtered_data.rename(
                columns={
                    "범죄대분류": "범죄 대분류",
                    "범죄중분류": "범죄 중분류"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "선택한 범죄 대분류의 데이터가 없습니다."
        )

else:

    st.info(
        "표시할 세부 범죄 데이터가 없습니다."
    )


st.divider()

st.caption(
    "데이터 출처: 사용자가 제공한 crime.csv 파일"
)
