
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from statsmodels.tsa.holtwinters import Holt


# ----------------------------------------
# 1. 페이지 설정
# ----------------------------------------

st.set_page_config(
    page_title="서울 기온 분석 및 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 분석 및 예측")
st.write(
    "1907년부터 2025년까지의 기온 데이터를 분석하고 "
    "세 가지 알고리즘으로 미래 기온을 예측합니다."
)


# ----------------------------------------
# 2. CSV 파일 불러오기
# ----------------------------------------

@st.cache_data
def load_data():

    file_path = Path(__file__).resolve().parent.parent / "temperature.csv"

    if not file_path.exists():
        file_path = Path("temperature.csv")

    if not file_path.exists():
        st.error("temperature.csv 파일을 찾을 수 없습니다.")
        st.stop()

    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        st.error("CSV 파일의 인코딩을 확인해 주세요.")
        st.stop()

    df.columns = df.columns.str.strip()

    return df


df = load_data()


# ----------------------------------------
# 3. 날짜 데이터 처리
# ----------------------------------------

def parse_dates(series):

    raw = series.astype(str).str.strip()

    # 일반적인 날짜 형식 먼저 처리
    parsed = pd.to_datetime(raw, errors="coerce")

    # Jan-07 형태의 월-연도 데이터 처리
    short_format = raw.str.match(
        r"^[A-Za-z]{3}-\d{2}$",
        na=False
    )

    if short_format.any():

        short_values = raw[short_format]

        month_year = []
        previous_year = None
        century = 1900

        for value in short_values:

            month_text, year_text = value.split("-")
            year_number = int(year_text)

            if previous_year is not None:
                if year_number < previous_year:
                    century += 100

            full_year = century + year_number

            month_year.append(
                pd.to_datetime(
                    f"{month_text}-{full_year}",
                    format="%b-%Y",
                    errors="coerce"
                )
            )

            previous_year = year_number

        parsed.loc[short_format] = month_year

    return parsed


if "일시" not in df.columns:
    st.error("CSV 파일에 '일시' 열이 없습니다.")
    st.stop()

df["날짜"] = parse_dates(df["일시"])


# ----------------------------------------
# 4. 평균기온 열 확인
# ----------------------------------------

temperature_candidates = [
    "평균기온(℃)",
    "평균기온",
    "평균 기온",
    "평균기온(°C)"
]

temperature_col = None

for col in temperature_candidates:
    if col in df.columns:
        temperature_col = col
        break

if temperature_col is None:
    st.error(
        "평균기온 열을 찾을 수 없습니다. "
        "CSV의 열 이름을 확인해 주세요."
    )
    st.write("현재 CSV 열 이름:", list(df.columns))
    st.stop()


df[temperature_col] = pd.to_numeric(
    df[temperature_col],
    errors="coerce"
)

df = df.dropna(subset=["날짜", temperature_col])

df["연도"] = df["날짜"].dt.year
df["월"] = df["날짜"].dt.month

# 1907~2025년 데이터만 사용
df = df[
    (df["연도"] >= 1907) &
    (df["연도"] <= 2025)
]


# ----------------------------------------
# 5. 월 선택
# ----------------------------------------

st.subheader("📅 분석할 월 선택")

selected_month = st.selectbox(
    "분석할 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda x: f"{x}월"
)


# 선택한 월의 연도별 평균기온 계산
monthly_data = df[
    df["월"] == selected_month
].groupby("연도")[temperature_col].mean()

monthly_data = monthly_data.sort_index()

if len(monthly_data) < 3:
    st.error("예측에 사용할 수 있는 데이터가 부족합니다.")
    st.stop()


# ----------------------------------------
# 6. 과거 기온 그래프
# ----------------------------------------

st.subheader(
    f"📈 {selected_month}월 연도별 평균기온"
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=monthly_data.index,
        y=monthly_data.values,
        mode="lines+markers",
        name="실제 평균기온",
        line=dict(color="royalblue", width=2)
    )
)

fig.update_layout(
    title=f"1907~2025년 {selected_month}월 평균기온",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    xaxis=dict(
        range=[1907, 2025],
        dtick=10
    ),
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------
# 7. 미래 예측 연도 선택
# ----------------------------------------

st.divider()

st.subheader("🔮 미래 평균기온 예측")

last_year = int(monthly_data.index.max())

prediction_year = st.number_input(
    "예측할 연도를 입력하세요.",
    min_value=last_year + 1,
    max_value=2200,
    value=min(last_year + 10, 2200),
    step=1
)

prediction_year = int(prediction_year)

future_years = np.arange(
    last_year + 1,
    prediction_year + 1
)

all_years = np.arange(
    int(monthly_data.index.min()),
    prediction_year + 1
)

# 결측 연도를 포함한 연속적인 데이터 구성
yearly_data = monthly_data.reindex(all_years)

# 과거 결측 연도 보간
yearly_data = yearly_data.interpolate(
    method="linear",
    limit_direction="both"
)

actual_years = monthly_data.index.to_numpy()
actual_values = monthly_data.values


# ----------------------------------------
# 8. 알고리즘 1: 선형회귀
# ----------------------------------------

X = actual_years.reshape(-1, 1)
y = actual_values

linear_model = LinearRegression()
linear_model.fit(X, y)

linear_prediction = linear_model.predict(
    all_years.reshape(-1, 1)
)


# ----------------------------------------
# 9. 알고리즘 2: 다항회귀
# ----------------------------------------

poly_model = make_pipeline(
    PolynomialFeatures(degree=2),
    LinearRegression()
)

poly_model.fit(X, y)

poly_prediction = poly_model.predict(
    all_years.reshape(-1, 1)
)


# ----------------------------------------
# 10. 알고리즘 3: Holt 지수평활
# ----------------------------------------

# 연속적인 연도 데이터 생성
complete_years = np.arange(
    int(monthly_data.index.min()),
    last_year + 1
)

complete_series = monthly_data.reindex(
    complete_years
)

complete_series = complete_series.interpolate(
    method="linear",
    limit_direction="both"
)

# Statsmodels가 지원하는 날짜 인덱스 생성
date_index = pd.date_range(
    start=f"{complete_years[0]}-01-01",
    periods=len(complete_series),
    freq="YS"
)

complete_series.index = date_index

# Holt 모델 학습
holt_model = Holt(
    complete_series,
    damped_trend=True,
    initialization_method="estimated"
)

holt_fit = holt_model.fit(
    optimized=True
)

# 미래 예측
holt_future = holt_fit.forecast(
    steps=len(future_years)
)

# 과거 적합값 + 미래 예측값
holt_prediction = np.concatenate([
    np.asarray(holt_fit.fittedvalues),
    np.asarray(holt_future)
])

# 그래프 길이 확인
assert len(holt_prediction) == len(all_years)


# ----------------------------------------
# 11. 세 가지 알고리즘 비교 그래프
# ----------------------------------------

st.subheader("📊 세 가지 예측 알고리즘 비교")

fig2 = go.Figure()

# 실제 기온
fig2.add_trace(
    go.Scatter(
        x=actual_years,
        y=actual_values,
        mode="lines",
        name="실제 평균기온",
        line=dict(color="black", width=2)
    )
)

# 선형회귀
fig2.add_trace(
    go.Scatter(
        x=all_years,
        y=linear_prediction,
        mode="lines",
        name="선형회귀",
        line=dict(color="red", dash="solid")
    )
)

# 다항회귀
fig2.add_trace(
    go.Scatter(
        x=all_years,
        y=poly_prediction,
        mode="lines",
        name="다항회귀",
        line=dict(color="green", dash="dash")
    )
)

# Holt 지수평활
fig2.add_trace(
    go.Scatter(
        x=all_years,
        y=holt_prediction,
        mode="lines",
        name="Holt 지수평활",
        line=dict(color="purple", dash="dot")
    )
)

# 실제 데이터와 예측 데이터 구분
fig2.add_vline(
    x=last_year,
    line_dash="dash",
    line_color="gray",
    annotation_text="예측 시작"
)

fig2.update_layout(
    title=f"{selected_month}월 평균기온 미래 예측 비교",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# ----------------------------------------
# 12. 예측 결과 비교
# ----------------------------------------

linear_result = float(linear_prediction[-1])
poly_result = float(poly_prediction[-1])
holt_result = float(holt_prediction[-1])

st.subheader(
    f"🌡️ {prediction_year}년 {selected_month}월 예측 결과"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "선형회귀",
        f"{linear_result:.2f} ℃"
    )

with col2:
    st.metric(
        "다항회귀",
        f"{poly_result:.2f} ℃"
    )

with col3:
    st.metric(
        "Holt 지수평활",
        f"{holt_result:.2f} ℃"
    )


# ----------------------------------------
# 13. 알고리즘 설명
# ----------------------------------------

st.divider()

st.subheader("📚 예측 알고리즘 설명")

with st.expander("1. 선형회귀 (Linear Regression)"):

    st.write("""
    과거 데이터의 전체적인 증가 또는 감소 추세를
    직선으로 표현하는 알고리즘입니다.

    - 장점: 계산이 간단하고 추세를 파악하기 쉽습니다.
    - 특징: 일정한 속도로 기온이 변화한다고 가정합니다.
    """)

with st.expander("2. 다항회귀 (Polynomial Regression)"):

    st.write("""
    과거 데이터의 곡선 형태를 학습하여
    미래 기온을 예측하는 알고리즘입니다.

    - 장점: 직선으로 표현하기 어려운 변화 추세를 반영합니다.
    - 특징: 선형회귀와 달리 곡선 형태의 예측이 가능합니다.
    """)

with st.expander("3. Holt 지수평활 (Holt's Exponential Smoothing)"):

    st.write("""
    과거 데이터의 수준과 추세를 반영하여
    미래 값을 예측하는 시계열 분석 알고리즘입니다.

    - 장점: 최근 데이터의 변화와 추세를 반영합니다.
    - 특징: 추세가 시간이 지나면서 약해지는 감쇠 추세를 적용합니다.
    """)


# ----------------------------------------
# 14. 주의사항
# ----------------------------------------

st.divider()

st.caption("""
※ 위 결과는 과거 기온 데이터의 통계적 패턴을 바탕으로 계산한 예측값입니다.
실제 미래 기온은 온실가스 배출, 기후변화, 자연적 변동 등
다양한 요인에 따라 달라질 수 있습니다.
""")
