import urllib.request
from bs4 import BeautifulSoup

# 해당 url의 html 문서 불러오기
url = "https://www.crummy.com/"
html_doc = urllib.request.urlopen(url)

# html 문서를 객체로 생성
soup = BeautifulSoup(html_doc, 'html.parser')

# html 문서 내용 확인
#  str 형태 + prettify() 통해 포맷 정리
print(soup.prettify()[:500])

# 특정 tag 호출(ex. 'a' 태그)
link_list = soup.find_all('a')

# link_list(tag)로 둘러싸인 문자열 10개 가져오기
# (해당하는 내용이 7개로, 7개만 출력)
for tag in link_list[0:10]:
    print(tag.text.strip())