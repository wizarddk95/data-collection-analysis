from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import os
import urllib.request

query = input('검색할 키워드를 입력하세요: ')

url = 'https://search.naver.com/search.naver?where=news&sm=tab_jum&query=' + query

response = requests.get(url)
html_text = response.text
soup = BeautifulSoup(html_text, 'html.parser')

# 뉴스 컨테이너 찾기
news_containers = soup.find_all('div', class_="sds-comps-base-layout sds-comps-full-layout Xjmc2FydT7OB9hmaylFX")
print(f'수집된 뉴스 개수: {len(news_containers)}')

# 이미지 저장을 위한 폴더 생성
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
img_folder = f'news_images_{timestamp}'
os.makedirs(img_folder, exist_ok=True)

# 데이터를 저장할 리스트
news_data = []

for idx, container in enumerate(news_containers):
    # 제목과 링크 추출
    title_link = container.find('a')
    if title_link:
        title = title_link.find('span', class_="sds-comps-text sds-comps-text-ellipsis-1 sds-comps-text-type-headline1").get_text()
        link = title_link.get('href')
        
        # 내용 추출
        content = container.find('span', class_="sds-comps-text sds-comps-text-ellipsis-3 sds-comps-text-type-body1")
        content_text = content.get_text() if content else "내용 없음"
        
        # 이미지 추출 및 저장
        img_tag = container.find('img')
        if img_tag and img_tag.get('src'):
            img_url = img_tag.get('src')
            try:
                # 이미지 파일명 생성 (인덱스와 타임스탬프 사용)
                img_filename = f'news_{idx}_{timestamp}.jpg'
                img_path = os.path.join(img_folder, img_filename)
                
                # 이미지 다운로드
                urllib.request.urlretrieve(img_url, img_path)
                img_url = img_path  # 저장된 이미지 경로를 데이터에 저장
            except Exception as e:
                print(f"이미지 다운로드 실패: {e}")
                img_url = "이미지 다운로드 실패"
        else:
            img_url = "이미지 없음"
        
        # 현재 시간 추가
        crawled_at = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 데이터를 딕셔너리로 저장
        news_data.append({
            'title': title,
            'link': link,
            'content': content_text,
            'img_url': img_url,
            'crawled_at': crawled_at
        })

# 데이터프레임 생성
df = pd.DataFrame(news_data)

# 데이터프레임 출력
print("\n수집된 뉴스 데이터프레임:")
print(df)

# CSV 파일로 저장
filename = f'news_{timestamp}.csv'
df.to_csv(filename, index=False, encoding='utf-8-sig')
print(f'\n데이터가 {filename} 파일로 저장되었습니다.')
print(f'이미지가 {img_folder} 폴더에 저장되었습니다.')


