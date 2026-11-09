
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 월별 기온분석")
st.write("원하는 월을 선택하여 연도별 최고기온과 최저기온을 비교해 보세요.")

# CSV 파일 읽기 함수
def load_data(file):
    for encoding in ["cp949", "euc-kr", "utf-8-sig"]:
        try:
            if hasattr(file, "seek"):
                file.seek(0)

            return pd.read_csv(file, encoding=encoding)

        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일의 인코딩을 확인해 주세요.")


# 파일 업로드
uploaded_file = st.sidebar.file_uploader(
    "기온 데이터 CSV 파일 업로드",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        df = load_data("temperature.csv")

except FileNotFoundError:
    st.error("temperature.csv 파일을 업로드해 주세요.")
    st.stop()

except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()


# 필요한 컬럼 확인
required_columns = [
    "일시",
    "최고기온(℃)",
    "최저기온(℃)"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 컬럼 이름이 올바르지 않습니다.")
    st.stop()


# 월 영문명과 숫자 연결
month_dict = {
    "Jan": 1, "Feb": 2, "Mar": 3,
    "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9,
    "Oct": 10, "Nov": 11, "Dec": 12
}

# 날짜 분리
df["월영문"] = df["일시"].astype(str).str[:3]
df["월"] = df["월영문"].map(month_dict)

# 두 자리 연도를 네 자리 연도로 변환
# 데이터의 시간 순서를 이용하여 세기를 구분
years = []
last_year = 1907

for date in df["일시"].astype(str):
    yy = int(date.split("-")[-1])

    year = (last_year // 100) * 100 + yy

    if year < last_year:
        year += 100

    years.append(year)
    last_year = year

df["연도"] = years

# 기온 데이터 숫자형 변환
df["최고기온(℃)"] = pd.to_numeric(
    df["최고기온(℃)"], errors="coerce"
)

df["최저기온(℃)"] = pd.to_numeric(
    df["최저기온(℃)"], errors="coerce"
)


# 월 선택
month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요.",
    month_names
)

selected_number = month_names.index(selected_month) + 1


# 선택한 월의 데이터 추출
month_data = df[df["월"] == selected_number].copy()

# 연도별 데이터 정리
result = month_data.groupby("연도", as_index=False).agg({
    "최고기온(℃)": "mean",
    "최저기온(℃)": "mean"
})

result = result.dropna(
    subset=["최고기온(℃)", "최저기온(℃)"]
)

result = result.sort_values("연도")


# 분석 결과 표시
st.subheader(f"📊 {selected_month} 연도별 기온 변화")

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

# 최고기온 그래프 (빨간색)
fig.add_trace(go.Scatter(
    x=result["연도"],
    y=result["최고기온(℃)"],
    mode="lines+markers",
    name="최고기온",
    line=dict(color="red", width=2),
    marker=dict(size=5)
))

# 최저기온 그래프 (파란색)
fig.add_trace(go.Scatter(
    x=result["연도"],
    y=result["최저기온(℃)"],
    mode="lines+markers",
    name="최저기온",
    line=dict(color="blue", width=2),
    marker=dict(size=5)
))

# 그래프 레이아웃
fig.update_layout(
    title={
        "text": "월별 기온분석",
        "x": 0.5
    },
    xaxis_title="연도",
    yaxis_title="온도 (℃)",
    legend_title="범례",
    hovermode="x unified",
    template="plotly_white",
    height=550
)

# 그래프 출력
st.plotly_chart(fig, use_container_width=True)


# 데이터 표 출력
with st.expander("📋 연도별 상세 데이터 확인하기"):
    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )

# 하단 안내
st.caption("자료 출처: temperature.csv")
st.caption("최고기온은 빨간색, 최저기온은 파란색으로 표시됩니다.")
