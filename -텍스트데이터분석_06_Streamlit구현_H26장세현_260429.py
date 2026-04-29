#   개발 환경 구축
import streamlit as st

st.title('Hello, Stramlit World')

name = "Seahyeon"
st.title(f"Hello, {name}~~~~ Welcom to Streamlit World!!!")

#   Write, Magic Command
import pandas as pd
df = pd.DataFrame({
    'A':[1, 2, 3, 4],
    'B':[10, 20, 30, 40]
    })

#   Text 출력
import time
text = st.title('텍스트가 변할 겁니다.')
time.sleep(2)
text.info('2초가 지났습니다.')

#   Text 출력
st.title("260429_Streamlit 과제")
st.header("Stramlit 구동")
st.subheader("기능 확인")
st.text("분석 결과 앱 반영")
st.success("그린라이트!")
st.warning("위험위험")
st.info("안내 드립니다.")
st.error("에러에러")

#   Input widgets
st.button("Go to gallery")

st.radio("머신러닝 방법", ['신경망', '랜덤 포레스트', 'SVM'])
st.checkbox("토큰화")
st.selectbox("기술통계", ['빈도분석','카이제곱','t-test'])
st.multiselect("regression analysis", ['linear','logistic'])
st.slider("1부터 10까지", 1, 10)
st.text_input("우체통")
st.number_input("동전통")

#   Form
with st.form('나의 폼'):
    name_01 = st.text_input("이름")
    age_01 = st.number_input("나이", step = 1)
    check_01 = st.checkbox("약관에 동의합니다.")
    sub_01 = st.form_submit_button('제출')

#   사용자 입력 폼 만들기
if sub_01:
    st.write(f'이름: {name_01}, 나이: {age_01}')
    if check_01: st.write("약관에 동의했습니다.")
    else: st.write("약관에 동의하지 않았습니다.")

# sidebar 속성
st.sidebar.header("설정")
name_02 = st.sidebar.text_input("이름을 입력하세요.")
age_02 = st.sidebar.slider('나이', 1, 100, 15)
color_02 = st.sidebar.radio("좋아하는 색상을 선택하세요.", ['빨강', '파랑', '초록'])

from matplotlib import font_manager, rc
import matplotlib.pyplot as plt
from konlpy.corpus import kolaw
from konlpy.tag import Okt
from collections import Counter
from wordcloud import WordCloud

#   텍스트 분석
@st.cache_data
def analyze_text():
    input_filename = 'constitution.txt'
    const_doc = kolaw.open(input_filename).read()

    t = Okt()

    my_tags = ['Noun', 'Verb', 'Adjective']
    my_stopwords = ['제', '하는', '때']

    tokens = [
        #   태그가 pos에 포함 안 되게
            word for word, tag in t.pos(const_doc) 
            if tag in my_tags and word not in my_stopwords and len(word) > 1
        ]    
    counter = Counter(tokens)
    return counter, const_doc, tokens

#   빈도수(const_counter) 및 원본텍스트(const_doc)
const_counter, const_doc, tokens = analyze_text()

st.subheader('데이터 분석 결과')
st.write(f'총 단어 수: {len(tokens)}')
st.write(f'상위 10개 단어: {dict(const_counter.most_common(10))}')

x = [word for word, count in const_counter.most_common(20)]
y = [count for word, count in const_counter.most_common(20)]

font_path = "c:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)

st.subheader('헌법 키워드_막대그래프')
fig1, ax1 = plt.subplots()
ax1.barh(x[::-1], y[::-1])
st.pyplot(fig1)

st.subheader('헌법 키워드_워드클라우드')

const_wc = WordCloud(
    font_path = font_path,
    width = 800,
    height = 600,
    max_words = 50,
    background_color = 'ivory'
)

const_wc = const_wc.generate(const_doc)

fig2, ax2 = plt.subplots()
ax2.imshow(const_wc, interpolation='bilinear')
ax2.axis('off')
st.pyplot(fig2)