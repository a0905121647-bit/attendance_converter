"""
出勤轉檔網站 - Streamlit 應用
"""

import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
import tempfile
import os
from datetime import datetime, time
from attendance_calculator import AttendanceProcessor


# 頁面配置
st.set_page_config(
    page_title="出勤轉檔系統",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化 Session State"""
    if "employee_times" not in st.session_state:
        st.session_state.employee_times = {
            "101": {"hour": 11, "minute": 0},  # 陳品璇
        }
    if "default_hour" not in st.session_state:
        st.session_state.default_hour = 8
    if "default_minute" not in st.session_state:
        st.session_state.default_minute = 0
    if "processed_data" not in st.session_state:
        st.session_state.processed_data = None
    if "break_min_interval" not in st.session_state:
        st.session_state.break_min_interval = 30
    if "break_max_interval" not in st.session_state:
        st.session_state.break_max_interval = 120


def main():
    init_session_state()
    
    # 標題
    st.title("📊 出勤轉檔系統")
    st.markdown("---")
    
    # 側邊欄 - 設定
    with st.sidebar:
        st.header("⚙️ 系統設定")
        
        st.subheader("預設起算時間")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.default_hour = st.number_input(
                "預設小時",
                min_value=0,
                max_value=23,
                value=st.session_state.default_hour,
                key="default_hour_input"
            )
        with col2:
            st.session_state.default_minute = st.number_input(
                "預設分鐘",
                min_value=0,
                max_value=59,
                value=st.session_state.default_minute,
                key="default_minute_input"
            )
        
        st.divider()
        st.subheader("員工特殊設定")
        
        # 顯示現有員工設定
        if st.session_state.employee_times:
            st.write("**已設定的員工：**")
            for emp_id, times in list(st.session_state.employee_times.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"考勤號碼 {emp_id}")
                with col2:
                    st.write(f"{times['hour']:02d}:{times['minute']:02d}")
                with col3:
                    if st.button("刪除", key=f"del_{emp_id}"):
                        del st.session_state.employee_times[emp_id]
                        st.rerun()
        
        st.divider()
        
        # 新增員工設定
        st.write("**新增員工特殊起算時間：**")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_emp_id = st.text_input("考勤號碼", key="new_emp_id")
        with col2:
            new_hour = st.number_input(
                "小時",
                min_value=0,
                max_value=23,
                value=8,
                key="new_hour"
            )
        with col3:
            new_minute = st.number_input(
                "分鐘",
                min_value=0,
                max_value=59,
                value=0,
                key="new_minute"
            )
        
        if st.button("新增員工設定"):
            if new_emp_id:
                st.session_state.employee_times[new_emp_id] = {
                    "hour": new_hour,
                    "minute": new_minute
                }
                st.success(f"已新增員工 {new_emp_id} 的起算時間：{new_hour:02d}:{new_minute:02d}")
                st.rerun()
            else:
                st.error("請輸入考勤號碼")
        
        st.divider()
        st.subheader("休息推估參數")
        st.session_state.break_min_interval = st.number_input(
            "最小間隔（分鐘）",
            min_value=1,
            max_value=180,
            value=st.session_state.break_min_interval,
            help="打卡間隔需 ≥ 此值才可能被判定為休息"
        )
        st.session_state.break_max_interval = st.number_input(
            "最大間隔（分鐘）",
            min_value=1,
            max_value=300,
            value=st.session_state.break_max_interval,
            help="打卡間隔需 ≤ 此值才可能被判定為休息"
        )
        
        st.info(
            "💡 **提示**\n\n"
            "- 預設起算時間：所有員工的預設工作開始時間\n"
            "- 員工特殊設定：覆蓋特定員工的起算時間\n"
            "- 陳品璇（考勤號碼 101）已預設為 11:00"
        )
    
    # 主要內容區
    tab1, tab2, tab3 = st.tabs(["📤 上傳與處理", "📋 預覽結果", "📥 下載匯出"])
    
    with tab1:
        st.header("上傳打卡檔案")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "選擇一個或多個 CSV 檔案",
                type=["csv"],
                accept_multiple_files=True,
                help="支援多檔上傳，系統會自動合併處理"
            )
        
        with col2:
            st.write("")
            st.write("")
            process_button = st.button("🔄 開始處理", use_container_width=True)
        
        if uploaded_files and process_button:
            try:
                with st.spinner("正在處理檔案..."):
                    # 合併所有 CSV
                    all_data = []
                    for uploaded_file in uploaded_files:
                        # 嘗試多種編碼
                        content = None
                        encodings = ['utf-8', 'big5', 'gb2312', 'latin-1', 'cp1252']
                        file_bytes = uploaded_file.read()
                        
                        for encoding in encodings:
                            try:
                                content = file_bytes.decode(encoding)
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        
                        if content is None:
                            st.error(f"❌ 無法讀取 {uploaded_file.name}，編碼不支援")
                            continue
                        
                        all_data.append(content)
                    
                    if not all_data:
                        st.error("❌ 沒有可處理的檔案")
                    else:
                        combined_csv = "\n".join(all_data)
                    
                    # 建立處理器
                    processor = AttendanceProcessor(
                        employee_start_times={
                            emp_id: (times["hour"], times["minute"])
                            for emp_id, times in st.session_state.employee_times.items()
                        }
                    )
                    
                    # 設定預設起算時間
                    processor.employee_start_times.setdefault(
                        None,
                        (st.session_state.default_hour, st.session_state.default_minute)
                    )
                    
                    # 處理資料
                    result_df = processor.process_csv(combined_csv)
                    st.session_state.processed_data = result_df
                    
                    st.success(f"✅ 成功處理 {len(uploaded_files)} 個檔案，共 {len(result_df)} 筆記錄")
                    
                    # 顯示統計資訊
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("總記錄數", len(result_df))
                    with col2:
                        st.metric("員工數", result_df["考勤號碼"].nunique())
                    with col3:
                        st.metric("工作日數", result_df["日期"].nunique())
                    with col4:
                        total_hours = result_df["實際工時"].sum()
                        st.metric("總工時", f"{total_hours:.1f} 小時")
                    
            except Exception as e:
                st.error(f"❌ 處理失敗：{str(e)}")
                st.info("請檢查 CSV 格式是否正確，必要欄位：姓名、考勤號碼、日期時間、簽到/退")
        
        # 顯示 CSV 格式範例
        with st.expander("📝 CSV 格式範例"):
            example_csv = """姓名,考勤號碼,日期時間,簽到/退
王小明,001,2024-01-15 08:30,簽到
王小明,001,2024-01-15 12:00,簽退
王小明,001,2024-01-15 13:00,簽到
王小明,001,2024-01-15 17:30,簽退
陳品璇,101,2024-01-15 11:15,簽到
陳品璇,101,2024-01-15 14:30,簽退
陳品璇,101,2024-01-15 15:00,簽到
陳品璇,101,2024-01-15 20:00,簽退"""
            st.code(example_csv, language="csv")
    
    with tab2:
        st.header("處理結果預覽")
        
        if st.session_state.processed_data is not None:
            df = st.session_state.processed_data
            
            # 顯示篩選選項
            col1, col2, col3 = st.columns(3)
            
            with col1:
                emp_options = list(df["考勤號碼"].unique())
                selected_emp = st.multiselect(
                    "篩選員工",
                    options=emp_options,
                    default=emp_options
                )
            
            with col2:
                date_options = sorted(list(df["日期"].unique()))
                selected_date = st.multiselect(
                    "篩選日期",
                    options=date_options,
                    default=date_options
                )
            
            with col3:
                show_all = st.checkbox("顯示所有欄位", value=True)
            
            # 篩選資料
            filtered_df = df[
                (df["考勤號碼"].isin(selected_emp)) &
                (df["日期"].isin(selected_date))
            ]
            
            if show_all:
                st.dataframe(filtered_df, use_container_width=True)
            else:
                display_cols = [
                    "日期", "姓名", "考勤號碼", "上班時間", "下班時間",
                    "實際工時", "加班時數"
                ]
                st.dataframe(filtered_df[display_cols], use_container_width=True)
            
            # 顯示統計資訊
            st.subheader("統計摘要")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**按員工統計**")
                emp_stats = filtered_df.groupby("姓名").agg({
                    "實際工時": "sum",
                    "加班時數": "sum",
                    "日期": "count"
                }).rename(columns={"日期": "工作日數"})
                st.dataframe(emp_stats, use_container_width=True)
            
            with col2:
                st.write("**按日期統計**")
                date_stats = filtered_df.groupby("日期").agg({
                    "實際工時": "sum",
                    "加班時數": "sum",
                    "考勤號碼": "count"
                }).rename(columns={"考勤號碼": "人數"})
                st.dataframe(date_stats, use_container_width=True)
        
        else:
            st.info("📌 請先在「上傳與處理」頁籤上傳並處理檔案")
    
    with tab3:
        st.header("匯出結果")
        
        if st.session_state.processed_data is not None:
            df = st.session_state.processed_data
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Excel 匯出
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="出勤記錄", index=False)
                    
                    # 調整欄寬
                    worksheet = writer.sheets["出勤記錄"]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                output.seek(0)
                
                st.download_button(
                    label="📥 下載 Excel 檔案",
                    data=output.getvalue(),
                    file_name=f"出勤記錄_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                # CSV 匯出
                csv_data = df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 下載 CSV 檔案",
                    data=csv_data,
                    file_name=f"出勤記錄_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            st.divider()
            st.subheader("匯出說明")
            st.markdown("""
            - **Excel 檔案**：推薦用於文中系統匯入，格式已最佳化
            - **CSV 檔案**：適合進一步處理或其他系統使用
            - 所有欄位順序已按照文中系統要求排列
            - 時間格式統一為 HH:MM
            - 工時以小時為單位，保留 2 位小數
            """)
        
        else:
            st.info("📌 請先在「上傳與處理」頁籤上傳並處理檔案")
    
    # 頁腳
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
        <p>出勤轉檔系統 v1.0 | 用於文中系統匯入 | 最後更新：2024年</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
