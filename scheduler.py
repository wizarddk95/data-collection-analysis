import schedule
import time
from crawler import crawl_all_stocks

def job():
    crawl_all_stocks(today_only=True)

schedule.every().day.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
