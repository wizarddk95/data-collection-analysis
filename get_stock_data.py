import yfinance as yf
from datetime import datetime, timedelta
from config import STOCK_CODE, SAVE_PATH
import os
from typing import Dict, Any
import pandas as pd

def get_stock_ticker(code: str) -> str:
    """종목 코드에 따라 적절한 yfinance 티커를 반환"""
    return code if code.startswith('^') else f"{code}.KS"

def process_stock_data(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """주가 데이터프레임을 처리하여 필요한 컬럼과 계산을 수행"""
    needed_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[needed_cols]
    
    # 시가, 고가, 저가, 종가를 적절한 소수점 자리로 변환
    price_cols = ['Open', 'High', 'Low', 'Close']
    if code.startswith('^'):
        # 주가지수는 소수점 둘째자리까지
        df[price_cols] = df[price_cols].round(2)
    else:
        # 개별주식은 소수점 첫째자리까지
        df[price_cols] = df[price_cols].round(1)
    
    df.index = df.index.date
    df.index.name = '일자'
    
    # 수익률과 거래량변화율 계산 (모두 소수점 둘째자리까지)
    df['수익률'] = round(df['Close'].pct_change() * 100, 2)
    df['거래량변화율'] = round(df['Volume'].pct_change() * 100, 2)
    
    # 당일 변동폭 계산 (고가-저가)
    df['당일변동폭'] = round(df['High'] - df['Low'], 1)
    # 당일 변동폭 비율 계산 (당일변동폭/시가 * 100)
    df['당일변동폭비율'] = round((df['당일변동폭'] / df['Open']) * 100, 2)
    
    return df

def save_stock_data(df: pd.DataFrame, code: str) -> None:
    """주가 데이터를 CSV 파일로 저장"""
    output_path = os.path.join(SAVE_PATH, f'stock_price_{code}.csv')
    df.to_csv(output_path, encoding='utf-8')
    print(f"Saved {code} data to {output_path}")

def main():
    # 종목 매핑 설정
    stock_mapping = {
        '^KS11': '코스피',
        '^KQ11': '코스닥'
    }
    stock_mapping.update({code: code for code in STOCK_CODE})
    
    # 데이터 수집 기간 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    # 각 종목의 주가 데이터 수집
    stock_data: Dict[str, pd.DataFrame] = {}
    for code, name in stock_mapping.items():
        try:
            ticker = get_stock_ticker(code)
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                print(f"[Warning] {code} ({name}): 데이터가 없습니다.")
                continue
                
            df = process_stock_data(df, code)
            stock_data[code] = df
            save_stock_data(df, code)
            
        except Exception as e:
            print(f"[Error] {code} ({name}) 데이터 수집 중 오류 발생: {str(e)}")
            continue
    
    # 수집된 데이터 요약 출력
    for code, df in stock_data.items():
        print(f"\n종목코드 {code} ({stock_mapping[code]}) 주가 데이터:")
        print(f"기간: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"행 수: {len(df)}")

if __name__ == "__main__":
    main()