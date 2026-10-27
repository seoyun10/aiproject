import streamlit as st
st.title('웹사이트 제작하기')
st.text_input('이름을 입력하시오')
st.selectbox('좋아하는 음식을 선택하시오',['크루아상','포카치아','바게트','크림빵'])
st.button('인사말 생성')
