import streamlit as st
st.title('웹사이트 제작하기')
a=st.text_input('이름을 입력하시오')
b=st.selectbox('좋아하는 빵을 선택하시오',['크루아상','포카치아','바게트','소금빵'])
if st.button('인사말 생성'):
  st.write('엄 엄 줴줴이야')
