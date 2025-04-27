import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re
from datetime import datetime, timedelta

# code = input("종목 코드를 입력하세요: ")
code = "009830"
url = f"https://finance.naver.com/item/board.naver?code={code}&page=1"

driver = webdriver.Chrome()
driver.get(url)
time.sleep(1)

columns = ['일자', '시각', '내용', '댓글 수', '닉네임', '조회수', '공감수', '비공감수']
result = []

# 현재 날짜에서 1달 전 날짜 계산
one_month_ago = datetime.now() - timedelta(days=30)

stop_collecting = False
current_page = 1

while not stop_collecting:
    # ✅ 1. 현재 페이지의 게시글 긁기
    trs = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/table[1]/tbody/tr')
    rows = [tr.text for tr in trs]

    for row in rows[1:]:
        if "클린봇" in row or "설정" in row:
            continue
        if not row.strip():
            continue

        split_row = row.split()
        date_str = split_row[0]

        try:
            post_date = datetime.strptime(date_str, "%Y.%m.%d")
        except ValueError:
            continue

        # 1달 전보다 오래된 글이면 수집 종료
        if post_date < one_month_ago:
            stop_collecting = True
            break

        time_str = split_row[1]
        body_parts = []
        reply_count = 0
        nickname = ""
        views = likes = dislikes = 0

        for item in split_row[2:]:
            if re.match(r'^\[\d+\]$', item):
                reply_count = int(item.strip('[]'))
            elif '****' in item:
                nickname = item
                break
            else:
                body_parts.append(item)

        if nickname:
            idx_nick = split_row.index(nickname)
            try:
                views = int(split_row[idx_nick + 1].replace(',', ''))
                likes = int(split_row[idx_nick + 2])
                dislikes = int(split_row[idx_nick + 3])
            except (IndexError, ValueError):
                pass

        body_text = ' '.join(body_parts)
        result.append([date_str, time_str, body_text, reply_count, nickname, views, likes, dislikes])

    if stop_collecting:
        print("한 달 전 게시글 발견, 수집 종료합니다.")
        break

    # ✅ 2. 다음 페이지로 이동
    current_page += 1
    
    # 현재 페이지가 10의 배수인 경우 다음 버튼 클릭
    if current_page % 10 == 1 and current_page != 1:
        try:
            next_button = driver.find_element(By.XPATH, '//td[@class="pgR"]/a')
            next_button.click()
            time.sleep(2)
            print(f"{current_page}페이지로 이동했습니다.")
        except:
            print("다음 버튼이 없어 수집 종료합니다.")
            break
    else:
        # 일반적인 페이지 이동
        try:
            page_buttons = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/table[2]/tbody/tr/td[2]/table/tbody/tr/td')
            for btn in page_buttons:
                if btn.text.strip() == str(current_page):
                    btn.find_element(By.TAG_NAME, 'a').click()
                    time.sleep(1)
                    print(f"{current_page}페이지로 이동했습니다.")
                    break
        except Exception as e:
            print(f"페이지 이동 실패: {e}")
            break

# ✅ 최종 저장
df = pd.DataFrame(result, columns=columns)
print(df)

# 저장 (선택)
df.to_csv("data.csv", index=False)

# 드라이버 종료
driver.quit()
