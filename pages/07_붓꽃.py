
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="AI 붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 AI 붓꽃 품종 예측 시스템")

st.markdown("""
꽃잎의 길이와 너비를 입력하고,
3가지 인공지능 알고리즘으로 붓꽃의 품종을 예측해 보세요!
""")

st.divider()


# ==========================================
# 2. 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():

    try:
        df = pd.read_csv("Iris.csv", encoding="cp949")
    except (UnicodeDecodeError, FileNotFoundError):
        try:
            df = pd.read_csv("Iris.csv", encoding="utf-8-sig")
        except FileNotFoundError:
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

    required = ["꽃잎길이", "꽃잎너비", "품종"]

    if not all(col in df.columns for col in required):
        raise ValueError(
            "CSV 파일에 꽃잎길이, 꽃잎너비, 품종 열이 필요합니다."
        )

    df = df[required].copy()

    df["꽃잎길이"] = pd.to_numeric(
        df["꽃잎길이"], errors="coerce"
    )

    df["꽃잎너비"] = pd.to_numeric(
        df["꽃잎너비"], errors="coerce"
    )

    df = df.dropna().reset_index(drop=True)

    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


X = df[["꽃잎길이", "꽃잎너비"]]
y = df["품종"]


# ==========================================
# 3. 알고리즘 설명
# ==========================================

st.subheader("🤖 분류 알고리즘 알아보기")

with st.expander("🌳 1. 랜덤 포레스트 (Random Forest)"):

    st.markdown("""
    **여러 개의 의사결정나무를 결합하는 알고리즘**

    - 여러 의사결정나무가 각각 품종을 예측합니다.
    - 각 나무의 예측 결과를 투표 방식으로 종합합니다.
    - 가장 많은 표를 얻은 품종을 최종 결과로 선택합니다.

    **장점:** 복잡한 데이터의 패턴을 학습하는 데 유용합니다.

    **분류 방식:** 여러 나무의 예측 결과를 종합합니다.
    """)

with st.expander("📐 2. 서포트 벡터 머신 (SVM)"):

    st.markdown("""
    **데이터 사이의 최적의 경계를 찾는 알고리즘**

    - 서로 다른 품종의 데이터를 구분할 경계를 학습합니다.
    - 경계와 가까운 데이터들을 중요하게 활용합니다.
    - 새로운 데이터가 어느 영역에 위치하는지 판단합니다.

    **장점:** 복잡한 분류 경계를 학습할 수 있습니다.

    **분류 방식:** 품종을 구분하는 결정 경계를 이용합니다.
    """)

with st.expander("📍 3. K-최근접 이웃 (KNN)"):

    st.markdown("""
    **가까운 데이터의 품종을 참고하는 알고리즘**

    - 새로운 데이터와 기존 데이터 사이의 거리를 계산합니다.
    - 가장 가까운 데이터 5개를 찾습니다.
    - 가장 많이 등장한 품종으로 분류합니다.

    **장점:** 원리를 이해하기 쉽고 직관적입니다.

    **분류 방식:** 가까운 5개 데이터의 다수결을 이용합니다.
    """)


# ==========================================
# 4. 알고리즘 모델 생성 및 정확도 평가
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

models = {
    "랜덤 포레스트": RandomForestClassifier(
        n_estimators=300,
        random_state=42
    ),

    "서포트 벡터 머신": make_pipeline(
        StandardScaler(),
        SVC(
            kernel="rbf",
            probability=True,
            random_state=42
        )
    ),

    "K-최근접 이웃": make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(n_neighbors=5)
    )
}

accuracies = {}
trained_models = {}

for name, model in models.items():

    model.fit(X_train, y_train)

    prediction = model.predict(X_test)

    accuracies[name] = accuracy_score(
        y_test,
        prediction
    )

    # 전체 데이터로 최종 학습
    model.fit(X, y)

    trained_models[name] = model


# ==========================================
# 5. 알고리즘 선택
# ==========================================

st.divider()

st.subheader("🧠 사용할 알고리즘 선택")

selected_algorithm = st.selectbox(
    "예측에 사용할 알고리즘을 선택하세요.",
    [
        "랜덤 포레스트",
        "서포트 벡터 머신",
        "K-최근접 이웃"
    ]
)

model = trained_models[selected_algorithm]

st.info(
    f"현재 선택된 알고리즘: {selected_algorithm}"
)


# ==========================================
# 6. 입력 범위 설정
# ==========================================

st.divider()

st.subheader("✏️ 꽃잎 크기 입력")

st.markdown("""
붓꽃 데이터에 포함된 측정 범위 안에서 값을 선택할 수 있습니다.
단위는 cm입니다.
""")

col1, col2 = st.columns(2)

with col1:

    petal_length = st.number_input(
        "🌸 꽃잎 길이",
        min_value=1.0,
        max_value=6.9,
        value=4.5,
        step=0.1,
        format="%.1f"
    )

    st.caption("입력 가능 범위: 1.0 ~ 6.9 cm")

with col2:

    petal_width = st.number_input(
        "🌸 꽃잎 너비",
        min_value=0.1,
        max_value=2.5,
        value=1.5,
        step=0.1,
        format="%.1f"
    )

    st.caption("입력 가능 범위: 0.1 ~ 2.5 cm")


# ==========================================
# 7. 품종 예측
# ==========================================

input_data = pd.DataFrame(
    [[petal_length, petal_width]],
    columns=["꽃잎길이", "꽃잎너비"]
)

predicted_species = model.predict(input_data)[0]

probabilities = model.predict_proba(input_data)[0]

class_names = model.classes_

probability_df = pd.DataFrame({
    "품종": class_names,
    "예측 확률": probabilities * 100
}).sort_values(
    "예측 확률",
    ascending=False
)

st.divider()

st.subheader("🔍 AI 예측 결과")

result1, result2 = st.columns(2)

with result1:

    st.metric(
        "예측 품종",
        predicted_species
    )

with result2:

    st.metric(
        "선택 알고리즘 정확도",
        f"{accuracies[selected_algorithm] * 100:.2f}%"
    )

st.success(
    f"AI가 예측한 품종은 {predicted_species}입니다!"
)


# ==========================================
# 8. 품종별 예측 확률
# ==========================================

st.subheader("📊 품종별 예측 확률")

st.bar_chart(
    probability_df.set_index("품종"),
    y="예측 확률",
    color="#36A86B"
)

for _, row in probability_df.iterrows():

    st.write(
        f"{row['품종']} : {row['예측 확률']:.2f}%"
    )

    st.progress(
        float(row["예측 확률"]) / 100
    )


# ==========================================
# 9. 3가지 알고리즘 정확도 비교
# ==========================================

st.divider()

st.subheader("🏆 알고리즘 성능 비교")

accuracy_df = pd.DataFrame({
    "알고리즘": list(accuracies.keys()),
    "정확도 (%)": [
        value * 100
        for value in accuracies.values()
    ]
})

st.bar_chart(
    accuracy_df.set_index("알고리즘"),
    y="정확도 (%)",
    color="#5799D1"
)

best_algorithm = max(
    accuracies,
    key=accuracies.get
)

st.write(
    f"현재 테스트 데이터에서 가장 높은 정확도를 보인 "
    f"알고리즘은 **{best_algorithm}**입니다."
)

st.caption(
    "정확도는 전체 데이터 중 테스트용으로 분리한 20%의 "
    "데이터를 이용해 평가했습니다."
)


# ==========================================
# 10. 분류 영역 시각화
# ==========================================

st.divider()

st.subheader("🎯 붓꽃 품종 분류 영역")

st.markdown("""
**그래프 읽는 방법**

- 배경 색상: 선택한 AI가 분류하는 품종 영역
- 원형 점: 기존 붓꽃 데이터
- 초록색 별: 사용자가 입력한 값
""")

# 그래프 범위
x_min = 0.8
x_max = 7.1

y_min = 0.0
y_max = 2.7

xx, yy = np.meshgrid(
    np.linspace(x_min, x_max, 300),
    np.linspace(y_min, y_max, 300)
)

grid = pd.DataFrame({
    "꽃잎길이": xx.ravel(),
    "꽃잎너비": yy.ravel()
})

# 분류 영역 예측
Z = model.predict(grid)

class_to_num = {
    name: i
    for i, name in enumerate(class_names)
}

Z_num = np.array([
    class_to_num[name]
    for name in Z
]).reshape(xx.shape)

# 그래프 생성
fig, ax = plt.subplots(figsize=(11, 7))

ax.contourf(
    xx,
    yy,
    Z_num,
    levels=np.arange(len(class_names) + 1) - 0.5,
    cmap="Pastel1",
    alpha=0.4
)

colors = [
    "#E57373",
    "#64B5F6",
    "#BA68C8"
]

# 기존 데이터 표시
for i, name in enumerate(class_names):

    subset = df[df["품종"] == name]

    ax.scatter(
        subset["꽃잎길이"],
        subset["꽃잎너비"],
        color=colors[i],
        label=name,
        s=50,
        alpha=0.75,
        edgecolors="white"
    )

# 사용자 입력 별 표시
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

ax.annotate(
    f"({petal_length:.1f}, {petal_width:.1f})",
    (petal_length, petal_width),
    xytext=(12, 15),
    textcoords="offset points",
    fontsize=11,
    fontweight="bold"
)

ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# 영어 축 이름 사용: 클라우드 한글 폰트 문제 방지
ax.set_xlabel("Petal Length (cm)", fontsize=12)
ax.set_ylabel("Petal Width (cm)", fontsize=12)

ax.set_title(
    f"Classification Map - {selected_algorithm}",
    fontsize=15
)

ax.legend()
ax.grid(alpha=0.2)

st.pyplot(fig)
plt.close(fig)


# ==========================================
# 11. AI가 이렇게 분류한 이유
# ==========================================

st.divider()

st.subheader("💡 AI는 왜 이렇게 판단했을까?")

st.write(
    f"""
    사용자가 입력한 값은 다음과 같습니다.

    - 꽃잎 길이: {petal_length:.1f} cm
    - 꽃잎 너비: {petal_width:.1f} cm

    선택한 알고리즘은 **{selected_algorithm}**이며,
    최종 예측 품종은 **{predicted_species}**입니다.
    """
)

st.markdown("### 품종별 예측 근거")

top_probability = probability_df.iloc[0]

st.info(
    f"""
    가장 높은 예측 확률은 {top_probability['품종']}이며,
    그 확률은 {top_probability['예측 확률']:.2f}%입니다.

    그래프에서 초록색 별이 위치한 곳의 배경 색상이
    해당 알고리즘이 판단한 분류 영역입니다.
    """
)

if selected_algorithm == "랜덤 포레스트":

    st.write("""
    **랜덤 포레스트의 판단 원리**

    여러 의사결정나무가 각각 품종을 예측하고,
    각 품종에 대한 투표 결과를 종합하여
    최종 품종을 결정합니다.
    """)

elif selected_algorithm == "서포트 벡터 머신":

    st.write("""
    **SVM의 판단 원리**

    학습된 결정 경계를 기준으로 입력값이
    어느 품종 영역에 속하는지 판단합니다.

    이 프로젝트는 RBF 커널을 사용하여
    곡선 형태의 복잡한 분류 경계도 학습할 수 있습니다.
    """)

elif selected_algorithm == "K-최근접 이웃":

    st.write("""
    **KNN의 판단 원리**

    입력값과 가까운 기존 데이터 5개를 찾고,
    가장 많이 나타나는 품종을 선택합니다.

    따라서 주변 데이터의 품종 분포가
    최종 예측에 중요한 영향을 줍니다.
    """)


# ==========================================
# 12. 데이터 확인
# ==========================================

with st.expander("📂 학습 데이터 확인"):

    st.dataframe(
        df,
        use_container_width=True
    )

    st.write("전체 데이터:", len(df), "개")

    st.write(
        df["품종"].value_counts()
    )


st.divider()

st.caption(
    "AI Iris Classification | Random Forest · SVM · KNN"
)
