
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from statsmodels.tsa.holtwinters import Holt


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="서울 기온 분석 및 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 분석 및 예측")

st.write("""
1907년부터 2025년까지의 서울 기온 데이터를 분석하고
결측치 처리 방법과 예측 알고리즘에 따른 결과를 비교합니다.
""")


# ==========================================
# 2. 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():

    file_path = Path(__file__).resolve().parent.parent / "temperature.csv"

    if not file_path.exists():
        file_path = Path("temperature.csv")

    if not file_path.exists():
        st.error("temperature.csv 파일을 찾을 수 없습니다.")
        st.stop()

    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    for encoding in encodings:
        try:
            data = pd.read_csv(file_path, encoding=encoding)
            return data
        except UnicodeDecodeError:
            continue

    st.error("CSV 파일의 인코딩을 확인해 주세요.")
    st.stop()


df = load_data()
df.columns = df.columns.str.strip()


# ==========================================
# 3. 날짜 데이터 처리
# ==========================================

def parse_dates(series):

    raw = series.astype(str).str.strip()

    parsed = pd.to_datetime(raw, errors="coerce")

    short_format = raw.str.match(
        r"^[A-Za-z]{3}-\d{2}$",
        na=False
    )

    if short_format.any():

        previous_year = None
        century = 1900
        converted = []

        for value in raw[short_format]:

            month_text, year_text = value.split("-")
            year_number = int(year_text)

            if (
                previous_year is not None
                and year_number < previous_year
            ):
                century += 100

            full_year = century + year_number

            converted.append(
                pd.to_datetime(
                    f"{month_text}-{full_year}",
                    format="%b-%Y",
                    errors="coerce"
                )
            )

            previous_year = year_number

        parsed.loc[short_format] = converted

    return parsed


if "일시" not in df.columns:
    st.error("CSV에 '일시' 열이 없습니다.")
    st.stop()

df["날짜"] = parse_dates(df["일시"])


# ==========================================
# 4. 평균기온 열 확인
# ==========================================

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
    st.error("평균기온 열을 찾을 수 없습니다.")
    st.write("현재 CSV 열:", list(df.columns))
    st.stop()


df[temperature_col] = pd.to_numeric(
    df[temperature_col],
    errors="coerce"
)

df = df.dropna(subset=["날짜"])

df["연도"] = df["날짜"].dt.year
df["월"] = df["날짜"].dt.month

df = df[
    (df["연도"] >= 1907) &
    (df["연도"] <= 2025)
]


# ==========================================
# 5. 월 선택
# ==========================================

st.divider()
st.subheader("📅 분석 조건 설정")

selected_month = st.selectbox(
    "분석할 월을 선택하세요.",
    range(1, 13),
    format_func=lambda x: f"{x}월"
)


# 연도별 월 평균기온 계산
monthly_data = (
    df[df["월"] == selected_month]
    .groupby("연도")[temperature_col]
    .mean()
)

# 1907~2025년 전체 연도 생성
all_history_years = np.arange(1907, 2026)

# 없는 연도는 NaN으로 표시
raw_series = monthly_data.reindex(
    all_history_years
)

missing_count = int(raw_series.isna().sum())

if raw_series.notna().sum() < 3:
    st.error("분석할 수 있는 기온 데이터가 부족합니다.")
    st.stop()

last_year = 2025


# ==========================================
# 6. 결측치 현황
# ==========================================

st.subheader("🔍 결측치 현황")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "전체 연도",
        f"{len(raw_series)}년"
    )

with col2:
    st.metric(
        "결측 연도",
        f"{missing_count}년"
    )

with col3:
    st.metric(
        "실제 데이터",
        f"{raw_series.notna().sum()}년"
    )


# 결측치 현황 그래프
missing_fig = go.Figure()

missing_fig.add_trace(
    go.Scatter(
        x=raw_series.index,
        y=raw_series.values,
        mode="markers",
        name="실제 기온",
        marker=dict(color="royalblue", size=5)
    )
)

missing_fig.add_trace(
    go.Scatter(
        x=raw_series.index[raw_series.isna()],
        y=[0] * missing_count,
        mode="markers",
        name="결측 연도",
        marker=dict(color="red", size=10, symbol="x")
    )
)

missing_fig.update_layout(
    title=f"{selected_month}월 연도별 평균기온 및 결측 현황",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white"
)

st.plotly_chart(
    missing_fig,
    use_container_width=True
)


# ==========================================
# 7. 결측치 처리 방법 선택
# ==========================================

st.divider()
st.subheader("🧩 결측치 처리 방법 선택")

missing_method = st.selectbox(
    "사용할 결측치 처리 방법을 선택하세요.",
    [
        "제거",
        "중앙값으로 대체",
        "선형보간법"
    ]
)


# 결측치 처리 함수
def process_missing(data, method):

    result = data.copy()

    if method == "제거":

        result = result.dropna()

    elif method == "중앙값으로 대체":

        median_value = result.median()

        if pd.isna(median_value):
            raise ValueError("중앙값을 계산할 데이터가 없습니다.")

        result = result.fillna(median_value)

    elif method == "선형보간법":

        result = result.interpolate(
            method="linear",
            limit_direction="both"
        )

    return result


processed_series = process_missing(
    raw_series,
    missing_method
)

if len(processed_series) < 3:
    st.error("결측치 처리 후 데이터가 부족합니다.")
    st.stop()

if processed_series.isna().any():
    st.error("결측치 처리 후에도 빈 데이터가 남아 있습니다.")
    st.stop()


st.success(
    f"선택한 처리 방법: {missing_method} "
    f"| 학습 데이터: {len(processed_series)}개"
)


# ==========================================
# 8. 처리된 데이터 시각화
# ==========================================

st.subheader("📈 결측치 처리 결과")

fig_processed = go.Figure()

fig_processed.add_trace(
    go.Scatter(
        x=raw_series.index,
        y=raw_series.values,
        mode="lines+markers",
        name="처리 전 데이터",
        line=dict(color="gray")
    )
)

fig_processed.add_trace(
    go.Scatter(
        x=processed_series.index,
        y=processed_series.values,
        mode="lines+markers",
        name="처리 후 데이터",
        line=dict(color="royalblue", width=2)
    )
)

fig_processed.update_layout(
    title=f"{selected_month}월 결측치 처리 전후 비교",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white"
)

st.plotly_chart(
    fig_processed,
    use_container_width=True
)


# ==========================================
# 9. 예측 연도 선택
# ==========================================

st.divider()
st.subheader("🔮 미래 기온 예측")

prediction_year = st.number_input(
    "예측할 연도를 입력하세요.",
    min_value=2026,
    max_value=2200,
    value=2035,
    step=1
)

prediction_year = int(prediction_year)

future_years = np.arange(
    2026,
    prediction_year + 1
)

plot_years = np.arange(
    1907,
    prediction_year + 1
)


# ==========================================
# 10. 알고리즘 선택
# ==========================================

st.subheader("⚙️ 예측 알고리즘 선택")

algorithm_options = [
    "선형회귀",
    "다항회귀",
    "Holt 지수평활"
]

selected_algorithms = st.multiselect(
    "비교할 알고리즘을 선택하세요. (여러 개 선택 가능)",
    algorithm_options,
    default=algorithm_options
)

if not selected_algorithms:
    st.warning("최소 하나의 알고리즘을 선택해 주세요.")
    st.stop()


# ==========================================
# 11. 예측 함수
# ==========================================

def predict_temperature(data, algorithm, target_year):

    train_years = data.index.to_numpy(dtype=int)
    train_values = data.to_numpy(dtype=float)

    future = np.arange(
        2026,
        target_year + 1
    )

    all_years = np.arange(
        1907,
        target_year + 1
    )

    X = train_years.reshape(-1, 1)
    y = train_values

    # --------------------------------------
    # 선형회귀
    # --------------------------------------

    if algorithm == "선형회귀":

        model = LinearRegression()
        model.fit(X, y)

        predictions = model.predict(
            all_years.reshape(-1, 1)
        )

        final_value = float(predictions[-1])

        return all_years, predictions, final_value

    # --------------------------------------
    # 다항회귀
    # --------------------------------------

    elif algorithm == "다항회귀":

        model = make_pipeline(
            PolynomialFeatures(degree=2),
            LinearRegression()
        )

        model.fit(X, y)

        predictions = model.predict(
            all_years.reshape(-1, 1)
        )

        final_value = float(predictions[-1])

        return all_years, predictions, final_value

    # --------------------------------------
    # Holt 지수평활
    # --------------------------------------

    elif algorithm == "Holt 지수평활":

        if len(train_values) < 3:
            raise ValueError(
                "Holt 알고리즘을 적용하기 위한 데이터가 부족합니다."
            )

        model = Holt(
            train_values,
            damped_trend=True,
            initialization_method="estimated"
        )

        fitted = model.fit(
            optimized=True
        )

        fitted_values = np.asarray(
            fitted.fittedvalues
        )

        future_values = np.asarray(
            fitted.forecast(
                steps=len(future)
            )
        )

        x_values = np.concatenate([
            train_years,
            future
        ])

        y_values = np.concatenate([
            fitted_values,
            future_values
        ])

        final_value = float(future_values[-1])

        return x_values, y_values, final_value


# ==========================================
# 12. 선택한 결측치 처리 + 알고리즘 예측
# ==========================================

st.divider()
st.subheader("📊 선택 조건에 따른 미래 기온 예측")

main_fig = go.Figure()

# 실제 데이터
main_fig.add_trace(
    go.Scatter(
        x=raw_series.dropna().index,
        y=raw_series.dropna().values,
        mode="markers",
        name="실제 평균기온",
        marker=dict(color="black", size=5)
    )
)

# 처리된 데이터
main_fig.add_trace(
    go.Scatter(
        x=processed_series.index,
        y=processed_series.values,
        mode="lines",
        name=f"결측치 처리: {missing_method}",
        line=dict(color="gray", dash="dot")
    )
)

main_results = {}

for algorithm in selected_algorithms:

    try:

        x_values, y_values, final_value = predict_temperature(
            processed_series,
            algorithm,
            prediction_year
        )

        main_results[algorithm] = final_value

        main_fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                name=algorithm
            )
        )

    except Exception as e:
        st.error(f"{algorithm} 예측 중 오류: {e}")


main_fig.add_vline(
    x=2025,
    line_dash="dash",
    line_color="gray",
    annotation_text="예측 시작"
)

main_fig.update_layout(
    title=f"{selected_month}월 평균기온 예측 비교",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(
    main_fig,
    use_container_width=True
)


# ==========================================
# 13. 최종 예측 결과
# ==========================================

st.subheader(
    f"🌡️ {prediction_year}년 {selected_month}월 예측 결과"
)

result_cols = st.columns(len(selected_algorithms))

for col, algorithm in zip(
    result_cols,
    selected_algorithms
):

    if algorithm in main_results:

        with col:
            st.metric(
                algorithm,
                f"{main_results[algorithm]:.2f} ℃"
            )


# ==========================================
# 14. 결측치 처리 방법별 예측 비교
# ==========================================

st.divider()

st.subheader("🔬 결측치 처리 방법에 따른 예측 결과 비교")

st.write("""
같은 예측 알고리즘을 사용하더라도 결측치를 어떻게 처리하는지에 따라
미래 기온 예측값이 달라질 수 있습니다.
아래 그래프에서 세 가지 방법의 결과를 비교할 수 있습니다.
""")


all_methods = [
    "제거",
    "중앙값으로 대체",
    "선형보간법"
]

comparison_results = []

for method in all_methods:

    try:

        comparison_data = process_missing(
            raw_series,
            method
        )

        for algorithm in selected_algorithms:

            x_values, y_values, final_value = predict_temperature(
                comparison_data,
                algorithm,
                prediction_year
            )

            comparison_results.append({
                "결측치 처리 방법": method,
                "알고리즘": algorithm,
                "예측 평균기온": final_value
            })

    except Exception as e:
        st.warning(
            f"{method} 비교 중 오류가 발생했습니다: {e}"
        )


comparison_df = pd.DataFrame(
    comparison_results
)


# ==========================================
# 15. 결측치 처리별 막대그래프
# ==========================================

if not comparison_df.empty:

    comparison_fig = go.Figure()

    for algorithm in selected_algorithms:

        algorithm_data = comparison_df[
            comparison_df["알고리즘"] == algorithm
        ]

        comparison_fig.add_trace(
            go.Bar(
                x=algorithm_data["결측치 처리 방법"],
                y=algorithm_data["예측 평균기온"],
                name=algorithm
            )
        )

    comparison_fig.update_layout(
        title=f"{prediction_year}년 예측값: 결측치 처리 방법별 비교",
        xaxis_title="결측치 처리 방법",
        yaxis_title="예측 평균기온 (℃)",
        barmode="group",
        template="plotly_white"
    )

    st.plotly_chart(
        comparison_fig,
        use_container_width=True
    )


# ==========================================
# 16. 예측 결과 비교표
# ==========================================

st.subheader("📋 예측 결과 비교표")

if not comparison_df.empty:

    result_table = comparison_df.pivot(
        index="결측치 처리 방법",
        columns="알고리즘",
        values="예측 평균기온"
    )

    st.dataframe(
        result_table.round(2),
        use_container_width=True
    )


# ==========================================
# 17. 알고리즘 설명
# ==========================================

st.divider()
st.subheader("📚 예측 알고리즘 설명")

with st.expander("1. 선형회귀"):

    st.write("""
    과거 데이터의 전체적인 증가 및 감소 추세를
    직선으로 학습하여 미래 값을 예측합니다.

    - 직선 형태의 추세를 표현합니다.
    - 계산이 간단하고 결과를 이해하기 쉽습니다.
    """)

with st.expander("2. 다항회귀"):

    st.write("""
    과거 데이터의 곡선 형태를 학습하여
    미래 기온을 예측합니다.

    - 직선으로 표현하기 어려운 변화 추세를 반영합니다.
    - 2차 다항식을 사용합니다.
    """)

with st.expander("3. Holt 지수평활"):

    st.write("""
    과거 데이터의 수준과 추세를 분석하여
    미래 기온을 예측하는 시계열 분석 방법입니다.

    - 최근 데이터의 변화와 추세를 반영합니다.
    - 감쇠 추세를 적용하여 장기 예측 시 추세가 약해지도록 합니다.
    - 결측치 제거 시 남은 관측값을 연속된 관측 순서로 학습하므로
      실제 연도 간격이 반영되지 않는 한계가 있습니다.
    """)


# ==========================================
# 18. 결측치 처리 방법 설명
# ==========================================

st.subheader("🧩 결측치 처리 방법 설명")

with st.expander("1. 제거"):

    st.write("""
    기온 데이터가 없는 연도를 학습 데이터에서 제외합니다.

    - 장점: 실제 관측값만 사용합니다.
    - 단점: 데이터가 줄어들어 학습 정보가 감소합니다.
    """)

with st.expander("2. 중앙값으로 대체"):

    st.write("""
    결측된 연도의 기온을 전체 관측값의 중앙값으로 채웁니다.

    - 장점: 데이터의 개수를 유지할 수 있습니다.
    - 단점: 실제 연도별 기온 변화가 반영되지 않을 수 있습니다.
    """)

with st.expander("3. 선형보간법"):

    st.write("""
    결측 연도의 앞뒤 관측값을 직선으로 연결하여
    중간 기온을 계산합니다.

    - 장점: 주변 연도의 기온 변화 추세를 반영합니다.
    - 단점: 급격한 기온 변화가 발생한 경우 실제 값과 차이가 날 수 있습니다.
    """)


# ==========================================
# 19. 주의사항
# ==========================================

st.divider()

st.caption("""
※ 본 프로그램은 과거 평균기온의 통계적 패턴을 바탕으로 예측합니다.
실제 미래 기온은 다양한 기후 요인의 영향을 받으므로
예측 결과가 실제 기온과 일치한다는 보장은 없습니다.

※ 결측치가 없는 경우에는 세 가지 처리 방법의 결과가 동일할 수 있습니다.
※ Holt 지수평활은 결측치 제거 시 관측값 사이의 실제 연도 간격을
   구분하지 못하므로 결과 해석에 주의해야 합니다.
""")
