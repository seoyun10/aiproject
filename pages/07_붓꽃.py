
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="AI 붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 AI 붓꽃 품종 예측 시스템")
st.markdown("""
꽃잎의 길이와 너비를 입력하면
인공지능이 붓꽃의 품종을 예측합니다.
""")

st.divider()


# --------------------------------------------------
# 2. 데이터 불러오기
# --------------------------------------------------

@st.cache_data
def load_data():

    file_path = Path("Iris.csv")

    if file_path.exists():

        df = pd.read_csv(file_path, encoding="cp949")

        required = [
            "꽃잎길이", "꽃잎너비", "품종"
        ]

        if not all(col in df.columns for col in required):
            raise ValueError(
                "CSV 파일의 열 이름을 확인해주세요."
            )

        df = df[required].copy()

    else:
        # CSV 파일이 없으면 sklearn 기본 데이터 사용
        iris = load_iris()

        df = pd.DataFrame({
            "꽃잎길이": iris.data[:, 2],
            "꽃잎너비": iris.data[:, 3],
            "품종": [
                iris.target_names[i]
                for i in iris.target
            ]
        })

        df["품종"] = df["품종"].map({
            "setosa": "Iris-setosa",
            "versicolor": "Iris-versicolor",
            "virginica": "Iris-virginica"
        })

    df["꽃잎길이"] = pd.to_numeric(
        df["꽃잎길이"], errors="coerce"
    )

    df["꽃잎너비"] = pd.to_numeric(
        df["꽃잎너비"], errors="coerce"
    )

    df = df.dropna().reset_index(drop=True)

    return df


df = load_data()

features = ["꽃잎길이", "꽃잎너비"]
X = df[features]
y = df["품종"]


# --------------------------------------------------
# 3. 랜덤 포레스트 모델 생성
# --------------------------------------------------

@st.cache_resource
def train_model():

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    model.fit(X_train, y_train)

    # 테스트 데이터로 정확도 평가
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    # 전체 데이터로 최종 예측 모델 학습
    final_model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    final_model.fit(X, y)

    return final_model, accuracy


model, accuracy = train_model()


# --------------------------------------------------
# 4. 사용자 입력
# --------------------------------------------------

st.subheader("✏️ 꽃잎 크기 입력")

col1, col2 = st.columns(2)

with col1:

    petal_length = st.number_input(
        "꽃잎 길이 (cm)",
        min_value=0.1,
        max_value=7.0,
        value=4.5,
        step=0.1
    )

with col2:

    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=0.0,
        max_value=2.5,
        value=1.5,
        step=0.1
    )


# --------------------------------------------------
# 5. 품종 예측
# --------------------------------------------------

input_data = pd.DataFrame(
    [[petal_length, petal_width]],
    columns=features
)

prediction = model.predict(input_data)[0]

probabilities = model.predict_proba(input_data)[0]

class_names = model.classes_

probability_df = pd.DataFrame({
    "품종": class_names,
    "예측 확률 (%)": probabilities * 100
}).sort_values(
    "예측 확률 (%)",
    ascending=False
)

st.divider()

st.subheader("🔍 AI 예측 결과")

result_col1, result_col2 = st.columns(2)

with result_col1:

    st.metric(
        "예측된 붓꽃 품종",
        prediction
    )

with result_col2:

    st.metric(
        "모델 테스트 정확도",
        f"{accuracy * 100:.2f}%"
    )

st.success(
    f"입력한 꽃잎 크기는 {prediction}으로 예측되었습니다."
)


# --------------------------------------------------
# 6. 예측 확률 시각화
# --------------------------------------------------

st.subheader("📊 품종별 예측 확률")

prob_chart = probability_df.set_index("품종")

st.bar_chart(
    prob_chart,
    y="예측 확률 (%)",
    color="#36A86B"
)

st.dataframe(
    probability_df.style.format({
        "예측 확률 (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 7. 분류 영역 그래프
# --------------------------------------------------

st.divider()

st.subheader("🎯 붓꽃 품종 분류 시각화")

st.markdown("""
- 배경 색상: AI가 예측하는 품종별 분류 영역
- 원형 점: 기존 붓꽃 데이터
- 초록색 별: 사용자가 입력한 꽃잎 크기
""")

# 그래프 범위 설정
x_min = max(0, min(X["꽃잎길이"].min() - 0.5, petal_length - 0.5))
x_max = max(X["꽃잎길이"].max() + 0.5, petal_length + 0.5)

y_min = max(0, min(X["꽃잎너비"].min() - 0.2, petal_width - 0.2))
y_max = max(X["꽃잎너비"].max() + 0.2, petal_width + 0.2)

# 격자 생성
xx, yy = np.meshgrid(
    np.linspace(x_min, x_max, 300),
    np.linspace(y_min, y_max, 300)
)

grid = pd.DataFrame({
    "꽃잎길이": xx.ravel(),
    "꽃잎너비": yy.ravel()
})

# 격자마다 품종 예측
Z = model.predict(grid)

# 품종을 숫자로 변환
class_to_num = {
    name: i for i, name in enumerate(class_names)
}

Z_num = np.array([
    class_to_num[name] for name in Z
]).reshape(xx.shape)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(11, 7))

# 품종별 분류 영역
ax.contourf(
    xx,
    yy,
    Z_num,
    levels=np.arange(len(class_names) + 1) - 0.5,
    alpha=0.25,
    cmap="Pastel1"
)

# 기존 데이터 표시
colors = ["#E57373", "#64B5F6", "#BA68C8"]

for i, name in enumerate(class_names):

    subset = df[df["품종"] == name]

    ax.scatter(
        subset["꽃잎길이"],
        subset["꽃잎너비"],
        color=colors[i],
        label=name,
        s=55,
        alpha=0.75,
        edgecolors="white"
    )

# 사용자 입력값 표시
ax.scatter(
    petal_length,
    petal_width,
    marker="*",
    color="#00C853",
    edgecolors="black",
    linewidths=1.2,
    s=450,
    label="사용자 입력값",
    zorder=10
)

# 입력값 좌표 표시
ax.annotate(
    f"입력값 ({petal_length:.1f}, {petal_width:.1f})",
    (petal_length, petal_width),
    xytext=(12, 15),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold"
)

ax.set_xlabel("꽃잎 길이 (cm)", fontsize=12)
ax.set_ylabel("꽃잎 너비 (cm)", fontsize=12)

ax.set_title(
    "랜덤 포레스트 붓꽃 품종 분류 영역",
    fontsize=15,
    fontweight="bold"
)

ax.legend()
ax.grid(alpha=0.2)

st.pyplot(fig)
plt.close(fig)


# --------------------------------------------------
# 8. 왜 해당 품종으로 분류되었을까?
# --------------------------------------------------

st.divider()

st.subheader("💡 AI가 이렇게 판단한 이유")

st.write(
    f"입력한 꽃잎 길이는 {petal_length:.1f}cm, "
    f"꽃잎 너비는 {petal_width:.1f}cm입니다."
)

st.write(
    f"랜덤 포레스트는 여러 의사결정나무의 투표를 종합하여 "
    f"최종적으로 {prediction}을 예측했습니다."
)

st.markdown("**품종별 예측 확률을 확인해보세요.**")

for _, row in probability_df.iterrows():

    st.write(
        f"{row['품종']} : {row['예측 확률 (%)']:.2f}%"
    )

    st.progress(
        float(row["예측 확률 (%)"]) / 100
    )


# --------------------------------------------------
# 9. 변수 중요도
# --------------------------------------------------

st.subheader("📌 품종 분류에 중요한 특징")

importance_df = pd.DataFrame({
    "특징": features,
    "중요도": model.feature_importances_
}).sort_values(
    "중요도",
    ascending=False
)

st.bar_chart(
    importance_df.set_index("특징"),
    color="#F4A261"
)

st.caption(
    "변수 중요도는 전체 데이터의 품종 분류에서 "
    "각 특징이 모델의 예측에 기여한 정도를 나타냅니다."
)


# --------------------------------------------------
# 10. 데이터 확인
# --------------------------------------------------

with st.expander("📂 학습에 사용한 데이터 확인"):

    st.dataframe(
        df,
        use_container_width=True
    )

    st.write("전체 데이터 개수:", len(df))

    st.write(
        "품종별 데이터 개수:"
    )

    st.write(
        df["품종"].value_counts()
    )


st.divider()

st.caption(
    "AI Iris Classification | Random Forest"
)
