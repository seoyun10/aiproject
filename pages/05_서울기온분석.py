
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온분석")
st.write("1907년부터 2026년까지의 월별 기온 변화를 분석합니다.")

# 데이터 불러오기
@st.cache_data
def load_data():
    for encoding in ["cp949", "euc-kr", "utf-8-sig"]:
        try:
            return pd.read_csv(
                "temperature.csv",
                encoding=encoding
            )
        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 인코딩을 확인해 주세요.")

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다: {e}")
    st.stop()

# 월 데이터 설정
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

# 월 추출
df["월영문"] = df["일시"].astype(str).str[:3]
df["월"] = df["월영문"].map(month_dict)

# 연도 추출 (1907~2026)
years = []
century = 1900
last_yy = None

for date in df["일시"].astype(str):
    yy = int(date.split("-")[-1])

    if last_yy is not None and yy < last_yy:
        century += 100

    years.append(century + yy)
    last_yy = yy

df["연도"] = years

# 기온 숫자 변환
for col in ["최고기온(℃)", "최저기온(℃)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 월 선택
selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요.",
    month_names
)

selected_number = month_names.index(selected_month) + 1

# 선택 월 데이터 추출
month_data = df[df["월"] == selected_number].copy()

# 연도별 최고기온 및 최저기온
result = month_data.groupby("연도").agg({
    "최고기온(℃)": "max",
    "최저기온(℃)": "min"
})

# 1907년부터 2026년까지 모든 연도 표시
all_years = pd.Index(
    range(1907, 2027),
    name="연도"
)

result = result.reindex(all_years)

# 제목
st.subheader(f"📊 {selected_month} 연도별 기온 분석")

# 평균 통계
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "최고기온 평균",
        f"{result['최고기온(℃)'].mean():.1f}℃"
    )

with col2:
    st.metric(
        "최저기온 평균",
        f"{result['최저기온(℃)'].mean():.1f}℃"
    )

# 그래프 생성
fig = go.Figure()

# 최고기온 - 빨간색
fig.add_trace(go.Scatter(
    x=result.index,
    y=result["최고기온(℃)"],
    mode="lines+markers",
    name="최고기온",
    line=dict(color="red", width=2),
    marker=dict(size=5),
    connectgaps=False
))

# 최저기온 - 파란색
fig.add_trace(go.Scatter(
    x=result.index,
    y=result["최저기온(℃)"],
    mode="lines+markers",
    name="최저기온",
    line=dict(color="blue", width=2),
    marker=dict(size=5),
    connectgaps=False
))

# 그래프 디자인
fig.update_layout(
    title={
        "text": "월별 기온분석",
        "x": 0.5
    },
    xaxis_title="연도",
    yaxis_title="온도 (℃)",
    legend_title="범례",
    template="plotly_white",
    hovermode="x unified",
    height=550
)

# 가로축 1907~2026년 고정
fig.update_xaxes(
    range=[1907, 2026],
    tickmode="linear",
    tick0=1907,
    dtick=10,
    showgrid=True
)

# 그래프 출력
st.plotly_chart(
    fig,
    use_container_width=True
)

# 상세 데이터
with st.expander("📋 연도별 상세 데이터 확인"):
    st.dataframe(
        result,
        use_container_width=True
    )

st.caption("자료 출처: temperature.csv")
st.caption("최고기온: 빨간색 | 최저기온: 파란색")
st.caption("분석 기간: 1907년 ~ 2026년")

