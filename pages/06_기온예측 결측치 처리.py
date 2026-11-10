
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

from statsmodels.tsa.holtwinters import Holt


# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="서울 미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 미래 기온 예측 시스템")
st.markdown(
    "1907년부터 2025년까지의 서울 기온 데이터를 분석하고 "
    "3가지 알고리즘으로 미래 기온을 예측합니다."
)

st.divider()


# ==========================================
# 2. 데이터 불러오기
# ==========================================
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

    raise ValueError("CSV 한글 인코딩을 확인해 주세요.")


try:
    df = load_data()

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# ==========================================
# 3. 데이터 전처리
# ==========================================
required_columns = [
    "일시",
    "평균기온(℃)"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 컬럼을 확인해 주세요.")
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


# 월 추출
df["월영문"] = df["일시"].astype(str).str[:3]
df["월"] = df["월영문"].map(month_dict)


# 연도 추출
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

df["평균기온(℃)"] = pd.to_numeric(
    df["평균기온(℃)"],
    errors="coerce"
)

df = df.dropna(
    subset=["연도", "월"]
)

df["연도"] = df["연도"].astype(int)


# 1907~2025년만 사용
df = df[
    (df["연도"] >= 1907) &
    (df["연도"] <= 2025)
]


# ==========================================
# 4. 사용자 입력
# ==========================================
st.sidebar.header("⚙️ 분석 설정")

selected_month = st.sidebar.selectbox(
    "분석할 월 선택",
    month_names,
    index=0
)

month_number = month_names.index(selected_month) + 1

target_year = st.sidebar.number_input(
    "예측할 미래 연도",
    min_value=2026,
    max_value=2100,
    value=2035,
    step=1
)

st.sidebar.info(
    "과거 데이터는 1907~2025년까지만 학습에 사용합니다."
)


# ==========================================
# 5. 선택한 월의 연도별 평균기온
# ==========================================
monthly_data = df[
    df["월"] == month_number
].copy()


yearly_data = (
    monthly_data
    .groupby("연도")["평균기온(℃)"]
    .mean()
    .sort_index()
    .dropna()
)


if len(yearly_data) < 3:
    st.error("예측에 필요한 기온 데이터가 부족합니다.")
    st.stop()


years_actual = yearly_data.index.to_numpy(dtype=int)
temps_actual = yearly_data.to_numpy(dtype=float)

last_year = int(years_actual.max())
first_year = int(years_actual.min())

if target_year <= last_year:
    st.error("예측 연도는 마지막 실제 관측 연도보다 커야 합니다.")
    st.stop()


# ==========================================
# 6. 과거 기온 그래프
# ==========================================
st.header("📈 1. 과거 기온 분석")

st.write(
    f"선택한 {selected_month}의 1907~2025년 평균기온 변화입니다."
)

fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=years_actual,
    y=temps_actual,
    mode="lines+markers",
    name="실제 평균기온",
    line=dict(
        color="black",
        width=2
    ),
    marker=dict(size=4)
))

fig1.update_layout(
    title=f"서울 {selected_month} 연도별 평균기온",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=450,
    hovermode="x unified"
)

fig1.update_xaxes(
    range=[1907, 2025],
    dtick=10
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# ==========================================
# 7. 알고리즘 학습
# ==========================================
st.header("🤖 2. 미래 평균기온 예측")

st.write(
    f"1907~{last_year}년의 {selected_month} 평균기온을 학습하여 "
    f"{int(target_year)}년까지 예측합니다."
)


# 예측에 사용할 연도
future_years = np.arange(
    last_year + 1,
    int(target_year) + 1
)

all_years = np.arange(
    first_year,
    int(target_year) + 1
)

# 연도 크기를 줄여 수치 안정성 확보
X = (years_actual - first_year).reshape(-1, 1)

X_all = (
    all_years - first_year
).reshape(-1, 1)

y = temps_actual


# ==========================================
# 알고리즘 1. 선형 회귀
# ==========================================
linear_model = LinearRegression()

linear_model.fit(X, y)

linear_prediction = linear_model.predict(X_all)


# ==========================================
# 알고리즘 2. 다항 회귀
# ==========================================
poly_model = make_pipeline(
    PolynomialFeatures(degree=2),
    LinearRegression()
)

poly_model.fit(X, y)

poly_prediction = poly_model.predict(X_all)


# ==========================================
# 알고리즘 3. 홀트 지수평활
# ==========================================
# 누락된 연도는 보간하여 학습에 사용
complete_years = np.arange(
    first_year,
    last_year + 1
)

complete_series = yearly_data.reindex(
    complete_years
)

complete_series = complete_series.interpolate(
    method="linear",
    limit_direction="both"
)

holt_model = Holt(
    complete_series,
    damped_trend=True,
    initialization_method="estimated"
)

holt_fit = holt_model.fit(
    optimized=True
)

holt_future = holt_fit.forecast(
    len(future_years)
)

holt_prediction = np.concatenate([
    np.asarray(holt_fit.fittedvalues),
    np.asarray(holt_future)
])


# ==========================================
# 8. 예측 그래프
# ==========================================
fig2 = go.Figure()


# 실제 기온
fig2.add_trace(go.Scatter(
    x=years_actual,
    y=temps_actual,
    mode="markers",
    name="실제 평균기온",
    marker=dict(
        color="black",
        size=5
    )
))


# 선형 회귀
fig2.add_trace(go.Scatter(
    x=all_years,
    y=linear_prediction,
    mode="lines",
    name="선형 회귀",
    line=dict(
        color="red",
        width=2.5
    )
))


# 다항 회귀
fig2.add_trace(go.Scatter(
    x=all_years,
    y=poly_prediction,
    mode="lines",
    name="다항 회귀",
    line=dict(
        color="green",
        width=2.5,
        dash="dash"
    )
))


# 홀트 지수평활
fig2.add_trace(go.Scatter(
    x=all_years,
    y=holt_prediction,
    mode="lines",
    name="홀트 지수평활",
    line=dict(
        color="blue",
        width=2.5,
        dash="dot"
    )
))


# 미래 예측 구간 표시
fig2.add_vrect(
    x0=last_year + 0.5,
    x1=int(target_year),
    fillcolor="orange",
    opacity=0.10,
    line_width=0,
    annotation_text="미래 예측 구간",
    annotation_position="top left"
)

# 실제 데이터와 예측 구간 구분
fig2.add_vline(
    x=last_year + 0.5,
    line_dash="dash",
    line_color="gray",
    annotation_text="예측 시작",
    annotation_position="top"
)


fig2.update_layout(
    title=f"서울 {selected_month} 미래 평균기온 예측",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    legend_title="예측 알고리즘",
    template="plotly_white",
    hovermode="x unified",
    height=600
)

fig2.update_xaxes(
    range=[first_year, int(target_year)],
    dtick=max(10, int((target_year - first_year) / 12))
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# ==========================================
# 9. 최종 예측값 비교
# ==========================================
st.subheader("🔮 예측 연도별 최종 결과")

linear_final = float(linear_prediction[-1])
poly_final = float(poly_prediction[-1])
holt_final = float(holt_prediction[-1])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "선형 회귀",
        f"{linear_final:.2f}℃"
    )

with col2:
    st.metric(
        "다항 회귀",
        f"{poly_final:.2f}℃"
    )

with col3:
    st.metric(
        "홀트 지수평활",
        f"{holt_final:.2f}℃"
    )


# ==========================================
# 10. 알고리즘별 설명
# ==========================================
st.header("📚 3. 예측 알고리즘 알아보기")

with st.expander("🔴 1. 선형 회귀 (Linear Regression)"):

    st.write("""
    과거 기온의 전체적인 변화 방향을 직선으로 학습하는 방법입니다.

    - 작동 방식: 연도와 평균기온 사이의 직선 관계를 계산합니다.
    - 그래프 특징: 일정한 기울기의 직선으로 나타납니다.
    - 장점: 계산이 간단하고 장기적인 상승·하락 추세를 파악하기 좋습니다.
    - 단점: 기온의 복잡한 곡선 변화는 충분히 반영하지 못합니다.
    """)

with st.expander("🟢 2. 다항 회귀 (Polynomial Regression)"):

    st.write("""
    과거 기온의 변화가 직선이 아닌 곡선으로 나타나는 특징을 학습합니다.

    - 작동 방식: 연도와 기온의 관계를 2차 곡선으로 표현합니다.
    - 그래프 특징: 위로 또는 아래로 휘어지는 곡선으로 나타납니다.
    - 장점: 직선으로 설명하기 어려운 변화 패턴을 반영할 수 있습니다.
    - 단점: 먼 미래로 갈수록 예측값이 지나치게 커지거나 작아질 수 있습니다.
    """)

with st.expander("🔵 3. 홀트 지수평활 (Holt's Exponential Smoothing)"):

    st.write("""
    최근 기온 변화와 장기적인 추세를 함께 반영하는 시계열 예측 방법입니다.

    - 작동 방식: 수준과 추세를 갱신하면서 다음 기온을 예측합니다.
    - 그래프 특징: 최근 변화와 추세를 반영하며, 완만한 추세로 이어질 수 있습니다.
    - 장점: 시간에 따른 변화 추세를 반영하기 좋습니다.
    - 단점: 계절성이나 장기적인 기후 구조 변화까지 자동으로 설명하지는 못합니다.
    """)


# ==========================================
# 11. 예측 결과 비교 표
# ==========================================
st.header("📋 4. 알고리즘 예측 결과 비교")

comparison = pd.DataFrame({
    "알고리즘": [
        "선형 회귀",
        "다항 회귀",
        "홀트 지수평활"
    ],
    "예측 연도": [
        int(target_year)
    ] * 3,
    "예측 평균기온(℃)": [
        linear_final,
        poly_final,
        holt_final
    ]
})

st.dataframe(
    comparison.style.format({
        "예측 평균기온(℃)": "{:.2f}"
    }),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 12. 마무리
# ==========================================
st.divider()

st.info(
    "주의: 예측 결과는 과거 기온의 통계적 패턴을 바탕으로 "
    "계산한 추정치이며 실제 미래 기온을 보장하지 않습니다. "
    "특히 먼 미래의 예측은 불확실성이 커집니다."
)

st.caption(
    "데이터 출처: temperature.csv | "
    "학습 기간: 1907~2025년"
)
