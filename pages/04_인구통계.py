
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from pathlib import Path

# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울시 연령별 인구 분석",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# 상위 폴더 경로 설정
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "popultion.csv"

PINK = "#FF1493"

# --------------------------------------------------
# 화면 디자인
# --------------------------------------------------
st.markdown("""
<style>
.main-title {
    font-size: 32px;
    font-weight: bold;
    color: #FF1493;
}
.sub-title {
    color: #777777;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<p class="main-title">📊 서울시 연령별 인구 분석</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="sub-title">행정구역, 성별, 연도를 선택하여 연령별 인구를 분석해 보세요.</p>',
    unsafe_allow_html=True
)

st.divider()

# --------------------------------------------------
# CSV 파일 읽기 및 한글 인코딩 처리
# --------------------------------------------------
def read_csv_safely(file):
    encodings = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]

    last_error = None

    for encoding in encodings:
        try:
            if isinstance(file, (str, Path)):
                return pd.read_csv(file, encoding=encoding)
            else:
                file.seek(0)
                return pd.read_csv(file, encoding=encoding)

        except UnicodeDecodeError as e:
            last_error = e

    raise ValueError(
        f"CSV 인코딩을 확인할 수 없습니다: {last_error}"
    )


# --------------------------------------------------
# 열 이름 정리
# --------------------------------------------------
def clean_columns(df):
    df.columns = [
        str(col).strip().replace("\ufeff", "")
        for col in df.columns
    ]
    return df


def find_column(columns, keywords):
    for col in columns:
        name = str(col).replace(" ", "").lower()

        if any(keyword in name for keyword in keywords):
            return col

    return None


# --------------------------------------------------
# 세로형 데이터 처리
# 행정구역, 성별, 연도, 나이, 인구수
# --------------------------------------------------
def normalize_long_format(df):
    df = clean_columns(df)

    area_col = find_column(
        df.columns,
        ["행정구역", "자치구", "지역"]
    )

    sex_col = find_column(
        df.columns,
        ["성별", "남녀별"]
    )

    year_col = find_column(
        df.columns,
        ["연도", "년도", "기준연도"]
    )

    age_col = find_column(
        df.columns,
        ["나이", "연령"]
    )

    population_col = find_column(
        df.columns,
        ["인구수", "인구"]
    )

    if not all([
        area_col,
        sex_col,
        year_col,
        age_col,
        population_col
    ]):
        return None

    result = df[
        [
            area_col,
            sex_col,
            year_col,
            age_col,
            population_col
        ]
    ].copy()

    result.columns = [
        "행정구역",
        "성별",
        "연도",
        "나이",
        "인구수"
    ]

    result["행정구역"] = (
        result["행정구역"].astype(str).str.strip()
    )

    result["성별"] = (
        result["성별"].astype(str).str.strip()
    )

    result["연도"] = (
        result["연도"].astype(str)
        .str.extract(r"(20\d{2})")[0]
    )

    result["나이"] = (
        result["나이"].astype(str)
        .str.extract(r"(\d+)")[0]
    )

    result["인구수"] = pd.to_numeric(
        result["인구수"].astype(str).str.replace(",", ""),
        errors="coerce"
    )

    result["연도"] = pd.to_numeric(
        result["연도"], errors="coerce"
    )

    result["나이"] = pd.to_numeric(
        result["나이"], errors="coerce"
    )

    result = result.dropna(
        subset=[
            "행정구역",
            "성별",
            "연도",
            "나이",
            "인구수"
        ]
    )

    result["연도"] = result["연도"].astype(int)
    result["나이"] = result["나이"].astype(int)

    return result


# --------------------------------------------------
# 가로형 데이터 처리
# --------------------------------------------------
def normalize_wide_format(df):
    df = clean_columns(df)

    area_col = find_column(
        df.columns,
        ["행정구역", "자치구", "지역"]
    )

    if area_col is None:
        return None

    records = []

    for _, row in df.iterrows():

        area = str(row[area_col]).strip()

        for col in df.columns:

            if col == area_col:
                continue

            col_name = str(col).replace(" ", "")

            year_match = re.search(
                r"(20\d{2})",
                col_name
            )

            age_match = re.search(
                r"(\d+)\s*세",
                col_name
            )

            if not year_match or not age_match:
                continue

            if "남자" in col_name or "남성" in col_name:
                sex = "남자"

            elif "여자" in col_name or "여성" in col_name:
                sex = "여자"

            else:
                continue

            value = pd.to_numeric(
                str(row[col]).replace(",", ""),
                errors="coerce"
            )

            if pd.isna(value):
                continue

            records.append({
                "행정구역": area,
                "성별": sex,
                "연도": int(year_match.group(1)),
                "나이": int(age_match.group(1)),
                "인구수": value
            })

    if not records:
        return None

    return pd.DataFrame(records)


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
st.subheader("📁 데이터 불러오기")

uploaded_file = st.file_uploader(
    "연령별 인구 데이터 CSV 파일 업로드",
    type=["csv"]
)

try:
    if uploaded_file is not None:

        raw_df = read_csv_safely(uploaded_file)

        st.success("업로드한 CSV 파일을 불러왔습니다.")

    elif DATA_FILE.exists():

        raw_df = read_csv_safely(DATA_FILE)

        st.success("상위 폴더의 CSV 파일을 불러왔습니다.")

    else:

        st.error(
            "popultion.csv 파일을 찾을 수 없습니다."
        )

        st.info(
            f"파일을 다음 위치에 넣어 주세요: {DATA_FILE}"
        )

        st.stop()

except Exception as e:

    st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 데이터 형식 변환
# --------------------------------------------------
df = normalize_long_format(raw_df)

if df is None:
    df = normalize_wide_format(raw_df)

if df is None or df.empty:

    st.warning(
        "현재 CSV 파일에서 연령별 인구 데이터를 찾지 못했습니다."
    )

    st.info(
        "연령별 인구 데이터에는 행정구역, 성별, 연도, 나이, 인구수가 필요합니다."
    )

    st.code("""
행정구역,성별,연도,나이,인구수
종로구,남자,2025,0,1200
종로구,남자,2025,1,1300
종로구,여자,2025,0,1100
""")

    st.caption("현재 CSV 파일의 열 이름")

    st.write(list(raw_df.columns))

    st.stop()


# --------------------------------------------------
# 성별 데이터 정리
# --------------------------------------------------
def normalize_sex(value):

    value = str(value).strip()

    if "남" in value:
        return "남자"

    elif "여" in value:
        return "여자"

    elif value in ["전체", "계", "합계"]:
        return "전체"

    return value


df["성별"] = df["성별"].apply(normalize_sex)


# --------------------------------------------------
# 분석 조건 선택
# --------------------------------------------------
st.subheader("🔍 분석 조건 선택")

col1, col2, col3 = st.columns(3)

with col1:

    areas = sorted(
        df["행정구역"].dropna().unique().tolist()
    )

    selected_area = st.selectbox(
        "행정구역 선택",
        areas
    )

with col2:

    sexes = sorted(
        df["성별"].dropna().unique().tolist()
    )

    selected_sex = st.selectbox(
        "성별 선택",
        sexes
    )

with col3:

    years = sorted(
        df["연도"].dropna().unique().tolist(),
        reverse=True
    )

    selected_year = st.selectbox(
        "연도 선택",
        years
    )


# --------------------------------------------------
# 선택한 조건에 맞는 데이터 추출
# --------------------------------------------------
filtered_df = df[
    (df["행정구역"] == selected_area) &
    (df["성별"] == selected_sex) &
    (df["연도"] == selected_year)
].copy()

filtered_df = filtered_df.sort_values("나이")


if filtered_df.empty:

    st.warning(
        "선택한 조건에 해당하는 데이터가 없습니다."
    )

    st.stop()


# --------------------------------------------------
# 주요 통계
# --------------------------------------------------
st.divider()

st.subheader("📌 분석 결과")

total_population = int(
    filtered_df["인구수"].sum()
)

max_age_row = filtered_df.loc[
    filtered_df["인구수"].idxmax()
]

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "총인구수",
    f"{total_population:,}명"
)

metric2.metric(
    "인구가 가장 많은 나이",
    f"{int(max_age_row['나이'])}세"
)

metric3.metric(
    "해당 연령 인구수",
    f"{int(max_age_row['인구수']):,}명"
)


# --------------------------------------------------
# 꺾은선 그래프
# --------------------------------------------------
st.divider()

st.subheader("📈 연령별 인구 꺾은선 그래프")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=filtered_df["나이"],
        y=filtered_df["인구수"],
        mode="lines+markers",
        name="인구수",

        line=dict(
            color=PINK,
            width=3
        ),

        marker=dict(
            color=PINK,
            size=7
        ),

        hovertemplate=(
            "나이: %{x}세<br>"
            "인구수: %{y:,.0f}명"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    title=dict(
        text=(
            f"{selected_area} {selected_sex} "
            f"{selected_year}년 연령별 인구"
        ),
        x=0.5,
        font=dict(size=20)
    ),

    xaxis_title="나이",
    yaxis_title="인구수",

    height=550,

    plot_bgcolor="white",
    paper_bgcolor="white",

    font=dict(
        family="Malgun Gothic, AppleGothic, NanumGothic, sans-serif",
        size=13
    ),

    hovermode="x unified"
)

# X축: 10살 단위 구분선
fig.update_xaxes(
    dtick=10,
    tick0=0,
    showgrid=True,
    gridcolor="#DDDDDD",
    gridwidth=1,
    zeroline=False
)

# Y축: 1,000만 단위 구분선
fig.update_yaxes(
    dtick=10_000_000,
    tick0=0,
    tickformat=",",
    showgrid=True,
    gridcolor="#DDDDDD",
    gridwidth=1,
    zeroline=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# 데이터 표
# --------------------------------------------------
st.divider()

st.subheader("📋 연령별 인구 데이터")

display_df = filtered_df[
    ["나이", "인구수"]
].copy()

display_df.columns = [
    "나이",
    "인구수"
]

display_df["인구수"] = display_df["인구수"].map(
    lambda x: f"{int(x):,}명"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# CSV 다운로드
# --------------------------------------------------
download_df = filtered_df[
    ["행정구역", "성별", "연도", "나이", "인구수"]
].copy()

csv_data = download_df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="📥 분석 결과 CSV 다운로드",
    data=csv_data,
    file_name="서울시_연령별_인구분석.csv",
    mime="text/csv"
)

st.caption(
    "※ 업로드하거나 불러온 연령별 인구 데이터를 기준으로 분석합니다."
)
