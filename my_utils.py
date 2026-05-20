def below_threshold_len(max_len, texts):
    count = 0
    for text in texts:
        if len(text.split()) <= max_len:
            count += 1
    print(f'길이가 {max_len} 이하인 text의 비율 : {(count / len(texts)) * 100:.2f}%')

def below_threshold_len_from_list(max_len, texts):
    count = 0
    for text in texts:
        if len(text) <= max_len:
            count += 1
    print(f'길이가 {max_len} 이하인 text의 비율 : {(count / len(texts)) * 100:.2f}%')


def cnt_word(word_count_list, max_len):
    total_cnt = 0
    rare_cnt = 0
    total_freq = 0
    rare_freq = 0

    for _, freq in word_count_list:# 단어와 빈도수가 tuple로
        total_cnt += 1
        total_freq += freq
        if freq < max_len:
            rare_cnt += 1
            rare_freq += freq
#    return [total_cnt, rare_cnt, total_freq, rare_freq]

    print(f'전체 단어 : {total_cnt : ,}개 {total_freq: ,}번')
    print(f'희귀 단어 (등장빈도 {max_len}번 미만) : {rare_cnt: ,}개 {rare_freq: ,}번')
    print(f'희귀 단어 비율 : 단어 수 {(rare_cnt/total_cnt) * 100:.2f}%/빈도 수 {(rare_freq/total_freq) * 100:.2f}%')
    use_cnt = total_cnt - rare_cnt
    use_freq = total_freq - rare_freq
    print(f'희귀 단어를 제외한 단어 수 : {total_cnt - rare_cnt:,}개 {(use_freq/total_freq) * 100:.2f}%')
