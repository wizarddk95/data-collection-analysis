# 완성형 최적화 코드
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

code = '009830'
base_url = f'https://finance.naver.com/item/board.naver?code={code}&page=1'

driver = webdriver.Chrome()
driver.get(base_url)

columns = ['일자', '시각', '제목', '본문', '댓글 수', '닉네임', '조회수', '공감수', '비공감수']
result = []

two_month_ago = datetime.now() - timedelta(days=60)
stop_collecting = False
current_page = 1

wait = WebDriverWait(driver, 5)

def wait_for_table():
    """게시글 테이블이 로드될 때까지 대기"""
    wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/div[3]/table[1]/tbody')))

def wait_for_body():
    """게시글 본문이 로드될 때까지 대기"""
    wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body"]')))

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
                    post_date = datetime.strptime(date_str, '%Y.%m.%d')
                except ValueError:
                    continue

                if post_date < two_month_ago:
                    stop_collecting = True
                    break

                time_str = split_row[1]
                title_parts = []
                reply_parts = []
                nickname = ''
                views = likes = dislikes = 0

                for item in split_row[2:]:
                    if re.match(r'^\[\d\]$', item):
                        reply_count = int(item.strip('[]'))
                    elif '****' in item:
                        nickname = item
                        break
                    else:
                        title_parts.append(item)

                if nickname:
                    idx_nick = split_row.index(nickname)
