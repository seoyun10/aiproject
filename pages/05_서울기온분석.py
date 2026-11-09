
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# =====================================
# 페이지 설정
# =====================================
st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 기온 분석")
st.write("서울의 장기간 기온 변화와 연도별 기온을 비교해 보세요.")

# =====================================
# 데이터 불러오기
# =====================================
def load_data(file):
    for encoding in ["cp949", "euc-kr", "utf-8-sig"]:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일의 한글 인코딩을 확인해 주세요.")


uploaded_file = st.sidebar.file_uploader(
    "기온 데이터 CSV 파일 업로드",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        df = load_data(io.BytesIO(uploaded_file.getvalue()))
    else:
        with open("temperature.csv", "rb") as f:
            df = load_data(f)

except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다: {e}")
    st.stop()


# =====================================
# 데이터 전처리
# =====================================
required_columns = [
    "일시",
    "평균기온(℃)",
    "최고기온(℃)",
    "최저기온(℃)"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 컬럼 이름을 확인해 주세요.")
    st.stop()

month_dict = {
    "Jan": 1, "Feb": 2, "Mar": 3,
    "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9,
    "Oct": 10, "Nov": 11, "Dec": 12
}

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

df["월영문"] = df["일시"].astype(str).str[:3]
df["월"] = df["월영문"].map(month_dict)

# 연도 추출
# 1907년부터 순서대로 연도를 계산
years = []
century = 1900
last_yy = None

for date in df["일시"].astype(str):
    try:
        yy = int(date.split("-")[-1])

        if last_yy is not None and yy < last_yy:
            century += 100

        years.append(century + yy)
        last_yy = yy

    except (ValueError, IndexError):
        years.append(None)

df["연도"] = years

# 숫자형 변환
temperature_columns = [
    "평균기온(℃)",
    "최고기온(℃)",
    "최저기온(℃)"
]

for col in temperature_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["연도", "월"])
df["연도"] = df["연도"].astype(int)

df = df[
    (df["연도"] >= 1907) &
    (df["연도"] <= 2026)
]


# =====================================
# 그래프 1. 전체 월별 평균기온
# =====================================
st.subheader("📈 서울 월별 평균기온")
st.write("전체 연도 데이터를 바탕으로 계산한 월별 평균기온입니다.")

monthly_avg = (
    df.groupby("월")["평균기온(℃)"]
    .mean()
    .reindex(range(1, 13))
)

fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=month_names,
    y=monthly_avg.values,
    mode="lines+markers",
    name="월별 평균기온",
    line=dict(color="orange", width=3),
    marker=dict(size=9),
    connectgaps=False
))

fig1.update_layout(
    title="서울의 월별 평균기온",
    xaxis_title="월",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=450,
    hovermode="x unified"
)

fig1.update_xaxes(
    categoryorder="array",
    categoryarray=month_names
)

st.plotly_chart(fig1, use_container_width=True)

st.divider()


# =====================================
# 그래프 2. 연도 선택 및 비교
# =====================================
st.subheader("📊 연도별 최고기온과 최저기온 비교")

st.write(
    "비교할 연도 수를 선택한 후 원하는 연도를 선택하세요."
)

year_count = st.radio(
    "연도 선택 개수",
    [1, 2],
    horizontal=True,
    format_func=lambda x: f"{x}개 선택"
)

available_years = sorted(df["연도"].unique().tolist())

if year_count == 1:

    selected_year = st.selectbox(
        "분석할 연도를 선택하세요.",
        available_years,
        index=len(available_years) - 1
    )

    selected_years = [selected_year]

else:

    col1, col2 = st.columns(2)

    with col1:
        year1 = st.selectbox(
            "첫 번째 연도",
            available_years,
            index=len(available_years) - 2
        )

    with col2:
        second_options = [
            y for y in available_years if y != year1
        ]

        year2 = st.selectbox(
            "두 번째 연도",
            second_options,
            index=len(second_options) - 1
        )

    selected_years = [year1, year2]


# =====================================
# 선택한 연도 데이터 추출
# =====================================
selected_data = df[
    df["연도"].isin(selected_years)
].copy()

# 연도와 월별 데이터 정리
yearly_data = selected_data.groupby(
    ["연도", "월"]
).agg({
    "최고기온(℃)": "mean",
    "최저기온(℃)": "mean"
}).reset_index()


# =====================================
# 비교 그래프 생성
# =====================================
fig2 = go.Figure()

line_styles = ["solid", "dash"]

for i, year in enumerate(selected_years):

    year_data = yearly_data[
        yearly_data["연도"] == year
    ].set_index("월").reindex(range(1, 13))

    # 최고기온
    fig2.add_trace(go.Scatter(
        x=month_names,
        y=year_data["최고기온(℃)"],
        mode="lines+markers",
        name=f"{year}년 최고기온",
        line=dict(
            color="red",
            width=2.5,
            dash=line_styles[i]
        ),
        marker=dict(size=7),
        connectgaps=False
    ))

    # 최저기온
    fig2.add_trace(go.Scatter(
        x=month_names,
        y=year_data["최저기온(℃)"],
        mode="lines+markers",
        name=f"{year}년 최저기온",
        line=dict(
            color="blue",
            width=2.5,
            dash=line_styles[i]
        ),
        marker=dict(size=7),
        connectgaps=False
    ))


# =====================================
# 그래프 디자인
# =====================================
fig2.update_layout(
    title="연도별 최고기온과 최저기온 비교",
    xaxis_title="월",
    yaxis_title="온도 (℃)",
    legend_title="범례",
    template="plotly_white",
    height=550,
    hovermode="x unified"
)

fig2.update_xaxes(
    categoryorder="array",
    categoryarray=month_names
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# =====================================
# 상세 데이터
# =====================================
with st.expander("📋 선택한 연도의 상세 데이터"):

    st.dataframe(
        yearly_data,
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.caption("자료 출처: 서울 기온 데이터 temperature.csv")
st.caption("분석 기간: 1907년 ~ 2026년")
