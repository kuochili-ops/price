
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("藥品成分查詢與價格變化分析")

# 上傳 CSV 檔案
uploaded_file = st.file_uploader("請上傳藥品資料 CSV 檔", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("檔案已成功載入！")

    # 使用者輸入成分關鍵字
    ingredient = st.text_input("請輸入欲查詢的成分（例如：OLANZAPINE 5 MG）")

    if ingredient:
        # 篩選成分
        filtered = df[df['成分'].str.contains(ingredient, case=False, na=False)]
        if not filtered.empty:
            # 取得所有相關藥品代號
            codes = filtered['藥品代號'].unique()
            st.write(f"查詢結果，共有 {len(codes)} 個藥品代號：")
            for code in codes:
                st.subheader(f"藥品代號：{code}")
                sub_df = filtered[filtered['藥品代號'] == code].copy()

                # 轉換有效起日為日期格式
                sub_df['有效起日'] = pd.to_datetime(sub_df['有效起日'], format='%y%m%d', errors='coerce')
                # 取得最早與最新的資料
                earliest = sub_df.sort_values('有效起日').iloc[0]
                latest = sub_df.sort_values('有效起日').iloc[-1]

                # 計算經歷時間
                if pd.notnull(earliest['有效起日']) and pd.notnull(latest['有效起日']):
                    days = (latest['有效起日'] - earliest['有效起日']).days
                else:
                    days = None

                # 計算價格降幅百分比
                try:
                    price_drop = (earliest['支付價'] - latest['支付價']) / earliest['支付價'] * 100
                except:
                    price_drop = None

                # 顯示指定欄位
                show_cols = [
                    '藥品代號', '藥品英文名稱', '藥品中文名稱', '成分', '單複方',
                    '支付價', '藥商', '製造廠名稱', '劑型', '藥品分類', '分類分組名稱', 'ATC代碼'
                ]
                latest_row = latest[show_cols]
                st.dataframe(pd.DataFrame([latest_row]))

                # 顯示價格變化資訊
                st.markdown(f"""
                - 最早有效起日：{earliest['有效起日'].date() if pd.notnull(earliest['有效起日']) else '無法解析'}
                - 最早價格：{earliest['支付價']}
                - 最新有效起日：{latest['有效起日'].date() if pd.notnull(latest['有效起日']) else '無法解析'}
                - 最新價格：{latest['支付價']}
                - 經歷時間：{days if days is not None else '無法計算'} 天
                - 價格降幅：{f"{price_drop:.2f}%" if price_drop is not None else '無法計算'}
                """)
        else:
            st.warning("查無符合成分的藥品資料。")
    else:
        st.info("請輸入成分關鍵字進行查詢。")
else:
    st.info("請先上傳 CSV 檔案。")
