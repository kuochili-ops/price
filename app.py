
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
                sub_df['支付價'] = pd.to_numeric(sub_df['支付價'], errors='coerce')

                # 只取解析成功的日期
                valid_dates = sub_df[sub_df['有效起日_解析'].apply(lambda x: isinstance(x, datetime))]
                if not valid_dates.empty:
                    earliest = valid_dates.sort_values('有效起日_解析').iloc[0]
                    latest = valid_dates.sort_values('有效起日_解析').iloc[-1]
                    # 經歷天數
                    days = (latest['有效起日_解析'] - earliest['有效起日_解析']).days
                    # 經歷年/月/日
                    delta = relativedelta(latest['有效起日_解析'], earliest['有效起日_解析'])
                    years = delta.years
                    months = delta.months
                    remain_days = delta.days
                    # 價格降幅計算（確保型別正確且不為零）
                    try:
                        earliest_price = float(earliest['支付價'])
                        latest_price = float(latest['支付價'])
                        if earliest_price != 0:
                            price_drop = (earliest_price - latest_price) / earliest_price * 100
                        else:
                            price_drop = None
                    except Exception:
                        price_drop = None
                    earliest_date_str = earliest['有效起日_解析'].strftime('%Y-%m-%d')
                    latest_date_str = latest['有效起日_解析'].strftime('%Y-%m-%d')
                else:
                    earliest = sub_df.iloc[0]
                    latest = sub_df.iloc[-1]
                    days = None
                    years = months = remain_days = None
                    price_drop = None
                    earliest_date_str = f"無法解析（原始值：{earliest['有效起日']}）"
                    latest_date_str = f"無法解析（原始值：{latest['有效起日']}）"

                # 顯示指定欄位（最新資料）
                show_cols = [
                    '藥品代號', '藥品英文名稱', '藥品中文名稱', '成分', '單複方',
                    '支付價', '藥商', '製造廠名稱', '劑型', '藥品分類', '分類分組名稱', 'ATC代碼'
                ]
                latest_row = latest[show_cols]
                st.dataframe(pd.DataFrame([latest_row]))

                # 顯示價格變化資訊
                st.markdown(f"""
- 最早有效起日：{earliest_date_str}
- 最早價格：{earliest['支付價']}
- 最新有效起日：{latest_date_str}
- 最新價格：{latest['支付價']}
- 經歷時間：{days if days is not None else '無法計算'} 天（約 {years if years is not None else '-'} 年 {months if months is not None else '-'} 月 {remain_days if remain_days is not None else '-'} 天）
- 價格降幅：{f"{price_drop:.2f}%" if price_drop is not None else '無法計算'}
""")

                # 歷次價格調整經歷時間與降幅
                history = valid_dates.sort_values('有效起日_解析').copy()
                history['前次有效起日'] = history['有效起日_解析'].shift(1)
                history['前次支付價'] = history['支付價'].shift(1)

                def calc_delta(row):
                    if isinstance(row['有效起日_解析'], datetime) and isinstance(row['前次有效起日'], datetime):
                        delta = relativedelta(row['有效起日_解析'], row['前次有效起日'])
                        days = (row['有效起日_解析'] - row['前次有效起日']).days
                        return f"{delta.years}年{delta.months}月{delta.days}天（{days}天）"
                    else:
                        return ""
                history['經歷時間'] = history.apply(calc_delta, axis=1)

                def calc_drop(row):
                    try:
                        if pd.notnull(row['前次支付價']) and row['前次支付價'] != 0:
                            drop = (row['前次支付價'] - row['支付價']) / row['前次支付價'] * 100
                            return f"{drop:.2f}%"
                        else:
                            return ""
                    except:
                        return ""
                history['降價幅度'] = history.apply(calc_drop, axis=1)

                # 只顯示有前次資料的變動
                result = history.loc[history['前次有效起日'].notnull(), [
                    '前次有效起日', '有效起日_解析', '前次支付價', '支付價', '經歷時間', '降價幅度'
                ]]
                result = result.rename(columns={
                    '前次有效起日': '前次有效起日',
                    '有效起日_解析': '本次有效起日',
                    '前次支付價': '前次價格',
                    '支付價': '本次價格'
                })

                st.markdown("#### 歷次價格調整經歷時間與降幅")
                st.dataframe(result)

                # 顯示解析失敗的日期
                fail_dates = sub_df[sub_df['有效起日_解析'].apply(lambda x: not isinstance(x, datetime))]
                if not fail_dates.empty:
                    st.warning("以下有效起日解析失敗：")
                    st.write(fail_dates[['有效起日', '有效起日_解析']])
        else:
            st.warning("查無符合成分的藥品資料。")
    else:
        st.info("請輸入成分關鍵字進行查詢。")
else:
    st.info("請先上傳 CSV 檔案。")
