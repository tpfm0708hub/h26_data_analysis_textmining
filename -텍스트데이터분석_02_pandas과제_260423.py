import pandas as pd

df_01 = pd.read_csv('./data/bccard_201906.csv')

"""1. 데이터 로딩 및 확인"""

"""1) 데이터 확인: 앞부분"""
print(f'데이터 앞부분: {df_01.head()}')
"""2) 데이터 확인: 뒷부분"""
print(f'데이터 뒷부분: {df_01.tail()}')
"""3) 데이터 확인: 데이터 수"""
print(f'데이터 수: {len(df_01)}')

"""2. 서울시 거주 및 비거주 고객비교 분석"""
df_02 = df_01.copy()
df_03 = df_01.copy()

df_02 = df_01[df_01['CSTMR_MEGA_CTY_NM']=='서울특별시']
df_03 = df_01[df_01['CSTMR_MEGA_CTY_NM']!='서울특별시']

result_01 = [
    [len(df_02), len(df_03)],
    [format(sum(df_02['AMT']), ','), format(sum(df_03['AMT']), ',')],
    [format(sum(df_02['CNT']), ','), format(sum(df_03['CNT']), ',')]
    ]

"""고객 수, 총 소비액, 카드 이용 건수"""
tbl_01 = pd.DataFrame(result_01, columns = ['서울시_거주', '서울시_비거주'])
print(tbl_01)

"""3. 편의점 소비 정보 분석"""
df_04 = df_01.copy()
df_04 = df_04[df_04['CTY_RGN_NM'] == '강남구']

"""1) 편의점 소비액, 서울특별시 소비액"""
print(f'편의점 소비액: {format(sum(df_01[df_01['TP_BUZ_NO'] == 4010]['AMT']), ',')}')
print(f'서울특별시 소비액: {format(sum(df_01[df_01['MEGA_CTY_NM'] == '서울특별시']['AMT']), ',')}')
"""2) 강남구 편의점 소비액"""
print(f'강남구 편의점 소비액: {format(sum(df_04['AMT']), ',')}')
"""3) 강남구 편의점 소비액 중 강남구 저주자와 비거주자의 소비액 비교"""
result_02 = [
    [format(sum(df_04[df_04['CSTMR_CTY_RGN_NM']=='강남구']['AMT']), ','), format(sum(df_04[df_04['CSTMR_CTY_RGN_NM']!='강남구']['AMT']), ',')]
    ]
tbl_02 = pd.DataFrame(
    result_02, columns = ['강남구_거주자', '강남구_비거주자']
)
print(tbl_02)

