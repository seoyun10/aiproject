
# ==========================================
# 알고리즘 3. 홀트 지수평활
# ==========================================

# 누락된 연도 보간
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

# 날짜 인덱스 지정 (오류 해결 핵심)
date_index = pd.date_range(
    start=f"{first_year}-01-01",
    periods=len(complete_series),
    freq="YS"
)

complete_series.index = date_index

# 홀트 모델 학습
holt_model = Holt(
    complete_series,
    damped_trend=True,
    initialization_method="estimated"
)

holt_fit = holt_model.fit(
    optimized=True
)

# 미래 기온 예측
holt_future = holt_fit.forecast(
    steps=len(future_years)
)

# 실제 학습 구간 + 미래 예측 구간 결합
holt_prediction = np.concatenate([
    np.asarray(holt_fit.fittedvalues),
    np.asarray(holt_future)
])

# 그래프 길이 확인
assert len(holt_prediction) == len(all_years)
