import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor
import time
import os
from datetime import datetime, timedelta
import re

from config import STOCK_CODE, COLLECT_MONTHS, SAVE_PATH

def collect_post_data(driver, post_link):
    """게시글 본문 데이터 수집 (순차적으로)"""
    body_text = "본문 수집 실패"
    try:
        driver.execute_script(f"window.open('{post_link}');")
        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="body"]')))
        body_text = driver.find_element(By.XPATH, '//*[@id="body"]').text
    except Exception as e:
        print(f"본문 수집 실패: {post_link} / {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    return body_text

def collect_stock_data(stock_code):
    """특정 종목 데이터 수집 (순차적으로 게시글 수집)"""
    print(f"종목 {stock_code} 데이터 수집 시작")
    base_url = f"https://finance.naver.com/item/board.naver?code={stock_code}&page=1"

    driver = webdriver.Chrome()
    driver.get(base_url)
    time.sleep(1)

    columns = ['일자', '시각', '제목', '본문', '댓글 수', '닉네임', '조회수', '공감수', '비공감수']
    result = []

    target_date = datetime.now() - timedelta(days=30 * COLLECT_MONTHS)
    stop_collecting = False
    current_page = 1

    while not stop_collecting:
        try:
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

                    if post_date < target_date:
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

                    # 🔥 여기서 본문을 순차적으로 읽음
                    body_text = collect_post_data(driver, post_link)

                    result.append([date_str, time_str, title_text, body_text, reply_count, nickname, views, likes, dislikes])

                except Exception as e:
                    print(f"게시글 수집 실패: {e}")
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    continue

            if stop_collecting:
                print(f"종목 {stock_code}: {COLLECT_MONTHS}달 전 게시글 발견, 수집 종료합니다.")
                break

            current_page += 1

            if current_page % 10 == 1 and current_page != 1:
                try:
                    next_button = driver.find_element(By.XPATH, '//td[@class="pgR"]/a')
                    next_button.click()
                    time.sleep(2)
                    print(f"종목 {stock_code}: {current_page}페이지로 이동했습니다.")
                except:
                    print(f"종목 {stock_code}: 다음 버튼이 없어 수집 종료합니다.")
                    break
            else:
                try:
                    page_buttons = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/table[2]/tbody/tr/td[2]/table/tbody/tr/td')
                    for btn in page_buttons:
                        if btn.text.strip() == str(current_page):
                            btn.find_element(By.TAG_NAME, 'a').click()
                            time.sleep(1)
                            break
                except Exception as e:
                    print(f"종목 {stock_code}: 페이지 이동 실패: {e}")
                    break

        except Exception as e:
            print(f"종목 {stock_code}: 페이지 수집 중 오류: {e}")
            break

    driver.quit()

    # 결과 저장
    df = pd.DataFrame(result, columns=columns)
    os.makedirs(SAVE_PATH, exist_ok=True)
    df.to_csv(f"{SAVE_PATH}stock_sentiment_{stock_code}.csv", index=False, encoding='utf-8-sig')
    print(f"✅ 종목 {stock_code} 데이터 수집 완료: {len(df)}건")

def main():
    """메인: 종목별 병렬 수집"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(collect_stock_data, STOCK_CODE)

if __name__ == "__main__":
    main()
