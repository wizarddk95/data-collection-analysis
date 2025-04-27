# selenium의 webdriver를 사용하기 위한 import
from selenium import webdriver
from selenium.webdriver.common.by import By

# selenium으로 키를 조작하기 위한 import
from selenium.webdriver.common.keys import Keys

# 페이지 로딩을 기다리는데에 사용할 time 모듈 import
import time

# 크롬 드라이버 실행
driver = webdriver.Chrome()

# 크롬 드라이버에 url 주소 넣고 실행
driver.get("https://finance.naver.com/")

# 페이지가 완전히 로딩되도록 1초간 기다리기 
time.sleep(1)

# 검색어 창을 찾아 search_box 변수에 저장 (By.CLASS_NAME 방식)
# search_box = driver.find_element(By.CLASS_NAME, 'search_input')

# 검색어 창을 찾아 search_box 변수에 저장 (By.XPATH 방식)
search_box = driver.find_element(By.XPATH, '//*[@id="stock_items"]')

search_box.send_keys("한화솔루션")
search_box.send_keys(Keys.ENTER)
time.sleep(1)