
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("藥品成分查詢與價格變化分析（民國曆日期支援）")

def parse_roc_date(roc_str):
    """民國曆7位數轉西元日期"""
    try:
        roc_str = str(roc_str)
        if len(roc_str) != 7 or not roc_str.isdigit():
            raise ValueError("格式錯誤")
        year = int(roc_str[:3]) + 1911
        month = int(roc_str[3:5])
        day = int(roc_str[5:7])
        return datetime(year, month, day)
    except Exception as e:
        return f"解析失敗: {roc_str} ({e})"

uploaded_file = st.file_uploader("請上傳藥品資料 CSV 檔", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("檔案已成功載入！")

    ingredient = st.text_input("請輸入欲查詢的成分（例如：OLANZAPINE 5 MG）")

    if ingredient:
        filtered = df[df['成分'].str.contains(ingredient, case=False, na=False)]
        if not filtered.empty:
            codes = filtered['藥品代號'].unique()
            st.write(f"查詢結果，共有 {len(codes)} 個藥品代號：")
            for code in codes:
                st.subheader(f"藥品代號：{code}")
                sub_df = filtered[filtered['藥品代號'] == code].copy()

                # 解析民國曆日期
                sub_df['有效起日_解析'] = sub_df['有效起日'].apply(parse_roc_date)

                # 只取解析成功的日期
                valid_dates = sub_df[sub_df['有效起日_解析'].apply(lambda x: isinstance(x, datetime))]
                if not valid_dates.empty:
                    earliest = valid_dates.sort_values('有效起日_解析').iloc[0]
                    latest = valid_dates.sort_values('有效起日_解析').iloc[-1]
                    days = (latest['有效起日_解析'] - earliest['有效起日_解析']).days
                    try:
                        price_drop = (earliest['支付價'] - latest['支付價']) / earliest['支付價'] * 100
                    except Exception:
