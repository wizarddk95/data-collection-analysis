import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, timedelta
import re
import os

code = "009830"
base_url = f"https://finance.naver.com/item/board.naver?code={code}&page=1"

driver = webdriver.Chrome()
driver.get(base_url)

columns = ['일자', '시각', '제목', '본문', '댓글 수', '닉네임', '조회수', '공감수', '비공감수']
result = []

one_month_ago = datetime.now() - timedelta(days=30)
stop_collecting = False
current_page = 1

wait = WebDriverWait(driver, 5)

def wait_for_table():
    """게시글 테이블이 로드될 때까지 대기"""
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[3]/table[1]/tbody')))

def wait_for_body():
    """게시글 본문이 로드될 때까지 대기"""
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body"]')))

while not stop_collecting:
    try:
        wait_for_table()
        trs = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/table[1]/tbody/tr')

        for tr in trs[1:]:
            try:
                row = tr.text
                if "클린봇" in row or "설정" in row or not row.strip():
                    continue

                split_row = row.split()
                date_str = split_row[0]

                try:
                    post_date = datetime.strptime(date_str, "%Y.%m.%d")
                except ValueError:
                    continue

                if post_date < one_month_ago:
                    stop_collecting = True
                    break

                time_str = split_row[1]
                title_parts = []
                reply_count = 0
                nickname = ''
                views = likes = dislikes = 0

                for item in split_row[2:]:
                    if re.match(r'^\[\d+\]$', item):
                        reply_count = int(item.strip('[]'))
                    elif '****' in item:
                        nickname = item
                        break
                    else:
                        title_parts.append(item)

                if nickname:
                    idx_nick = split_row.index(nickname)
                    try:
                        views = int(split_row[idx_nick + 1].replace(',', ''))
                        likes = int(split_row[idx_nick + 2])
                        dislikes = int(split_row[idx_nick + 3])
                    except (IndexError, ValueError):
                        pass

                title_text = ' '.join(title_parts)

                post_link = tr.find_element(By.XPATH, './/td[2]/a').get_attribute('href')

                # 본문 새 탭 열기
                driver.execute_script(f"window.open('{post_link}');")
                driver.switch_to.window(driver.window_handles[-1])

                try:
                    wait_for_body()
                    body_text = driver.find_element(By.XPATH, '//*[@id="body"]').text
                except (TimeoutException, NoSuchElementException):
                    body_text = "본문 수집 실패"

                result.append([date_str, time_str, title_text, body_text, reply_count, nickname, views, likes, dislikes])

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print(f"⚠️ 게시글 수집 중 오류: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue

    except Exception as e:
        print(f"⚠️ 페이지 수집 중 오류: {e}")
        break

    if stop_collecting:
        print("✅ 한 달 전 게시글 발견, 수집 종료합니다.")
        break

    current_page += 1

    # 페이지 이동
    try:
        if current_page % 10 == 1 and current_page != 1:
            next_button = driver.find_element(By.XPATH, '//td[@class="pgR"]/a')
            next_button.click()
            print(f"➡️ {current_page}페이지로 이동했습니다.")
        else:
            page_buttons = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/table[2]/tbody/tr/td[2]/table/tbody/tr/td')
            for btn in page_buttons:
                if btn.text.strip() == str(current_page):
                    btn.find_element(By.TAG_NAME, 'a').click()
                    print(f"➡️ {current_page}페이지로 이동했습니다.")
                    break
    except Exception as e:
        print(f"⚠️ 페이지 이동 실패: {e}")
        break

# 결과 저장
df = pd.DataFrame(result, columns=columns)
print(df)

# 저장 디렉토리 준비
os.makedirs("../data", exist_ok=True)
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
save_path = f"../data/stock_sentiment_{current_time}.csv"
df.to_csv(save_path, index=False, encoding='utf-8-sig')
print(f"✅ 데이터 저장 완료: {save_path}")

driver.quit()
