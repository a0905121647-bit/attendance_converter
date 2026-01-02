"""
出勤轉檔核心計算模組
負責處理打卡資料的解析、工時計算、休息推估等邏輯
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import re


class AttendanceRecord:
    """單筆打卡記錄"""
    def __init__(self, name: str, emp_id: str, datetime_str: str, check_type: str):
        self.name = name
        self.emp_id = emp_id
        self.datetime_str = datetime_str
        self.check_type = check_type  # "簽到" or "簽退"
        self.datetime = self._parse_datetime(datetime_str)
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析各種日期時間格式"""
        datetime_str = str(datetime_str).strip()
        
        # 移除機器代碼（例如 "A12P12"）
        datetime_str = re.sub(r'\s+[A-Z0-9]+\s+', ' ', datetime_str)
        
        # 嘗試多種格式
        formats = [
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d %H:%M",
            "%m-%d %H:%M",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        return None


class DailyAttendance:
    """單日出勤記錄"""
    def __init__(self, name: str, emp_id: str, date: datetime, records: List[AttendanceRecord],
                 start_time_hour: int = 8, start_time_minute: int = 0):
        self.name = name
        self.emp_id = emp_id
        self.date = date
        self.records = sorted(records, key=lambda r: r.datetime if r.datetime else datetime.max)
        self.start_time_hour = start_time_hour
        self.start_time_minute = start_time_minute
        
        # 計算結果
        self.check_in_time = None
        self.check_out_time = None
        self.break_start = None
        self.break_end = None
        self.break_minutes = 0
        self.actual_hours = 0
        self.overtime_hours = 0
        self.remarks = ""
        
        self._calculate()
    
    def _calculate(self):
        """執行所有計算"""
        if not self.records or not any(r.datetime for r in self.records):
            self.remarks = "無有效打卡記錄"
            return
        
        # 過濾有效記錄
        valid_records = [r for r in self.records if r.datetime]
        if not valid_records:
            self.remarks = "無有效打卡記錄"
            return
        
        # 上班時間 = 當日最早的打卡時間（不受起算時間影響）
        self.check_in_time = valid_records[0].datetime
        
        # 下班時間以當日最後一筆打卡為準
        self.check_out_time = valid_records[-1].datetime
        
        # 推估中間休息
        self._estimate_break(valid_records)
        
        # 計算實際工時
        self._calculate_hours()
    
    def _estimate_break(self, records: List[AttendanceRecord]):
        """推估中間休息時間"""
        if len(records) < 2:
            return
        
        # 檢查相鄰打卡間隔
        for i in range(len(records) - 1):
            r1 = records[i]
            r2 = records[i + 1]
            
            if not r1.datetime or not r2.datetime:
                continue
            
            interval_minutes = (r2.datetime - r1.datetime).total_seconds() / 60
            
            # 檢查條件：
            # 1. 間隔 >= 30 分鐘 且 <= 120 分鐘
            # 2. 前一筆打卡時間落在 10:30–14:30
            if 30 <= interval_minutes <= 120:
                r1_time = r1.datetime.time()
                if datetime.strptime("10:30", "%H:%M").time() <= r1_time <= datetime.strptime("14:30", "%H:%M").time():
                    self.break_start = r1.datetime
                    self.break_end = r2.datetime
                    self.break_minutes = int(interval_minutes)
                    
                    # 若推估出的休息分鐘數 < 60 分鐘，一律以 60 分鐘計
                    if self.break_minutes < 60:
                        self.break_minutes = 60
                    break
        
        # 如果沒有找到休息記錄，則推估：工作 4 小時後休息 1 小時
        if self.break_minutes == 0 and self.check_in_time and self.check_out_time:
            # 上班時間 + 4 小時 = 休息開始時間
            break_start_time = self.check_in_time + timedelta(hours=4)
            # 檢查是否在工作時間內（下班時間之前）
            if break_start_time < self.check_out_time:
                self.break_start = break_start_time
                self.break_end = break_start_time + timedelta(hours=1)
                self.break_minutes = 60
    
    def _calculate_hours(self):
        """計算實際工時與加班時數"""
        if not self.check_in_time or not self.check_out_time:
            return
        
        # 實際工時 = (下班時間 - 上班起算時間) - 休息分鐘
        total_minutes = (self.check_out_time - self.check_in_time).total_seconds() / 60
        actual_minutes = total_minutes - self.break_minutes
        
        self.actual_hours = actual_minutes / 60
        
        # 加班時數 = 超過 8 小時的部分
        if self.actual_hours > 8:
            self.overtime_hours = self.actual_hours - 8
        else:
            self.overtime_hours = 0
    

    def _round_time_to_hour(self, dt: datetime, start_time_hour: int = 8, start_time_minute: int = 0) -> datetime:
        """將時間無條件進位到整點（除非是遲到）"""
        if not dt:
            return dt
        
        # 起算時間
        start_time = dt.replace(hour=start_time_hour, minute=start_time_minute, second=0, microsecond=0)
        
        # 如果已經超過起算時間（遲到），保持原時間但捨去分鐘
        if dt >= start_time:
            return dt.replace(minute=0, second=0, microsecond=0)
        
        # 如果還沒到起算時間，無條件進位到起算時間的整點
        # 如果分鐘 > 0，進位到下一小時；否則保持原時間
        if dt.minute > 0 or dt.second > 0:
            return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            return dt.replace(minute=0, second=0, microsecond=0)

    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        # 無條件進位上班時間到整點（除非是遲到）
        check_in_rounded = self._round_time_to_hour(self.check_in_time, self.start_time_hour, self.start_time_minute) if self.check_in_time else None
        # 下班時間保持原始打卡時間（不進位）
        check_out_rounded = self.check_out_time
        
        return {
            "日期": self.date.strftime("%Y/%m/%d") if self.date else "",
            "姓名": self.name,
            "考勤號碼": self.emp_id,
            "上班時間": check_in_rounded.strftime("%H:%M") if check_in_rounded else "",
            "下班時間": check_out_rounded.strftime("%H:%M") if check_out_rounded else "",
            "休息開始": self.break_start.strftime("%H:%M") if self.break_start else "",
            "休息結束": self.break_end.strftime("%H:%M") if self.break_end else "",
            "休息分鐘數": self.break_minutes,
            "實際工時": round(self.actual_hours, 2),
            "加班時數": round(self.overtime_hours, 2),
            "備註": self.remarks,
        }


class AttendanceProcessor:
    """出勤資料處理器"""
    
    def __init__(self, employee_start_times: Dict[str, Tuple[int, int]] = None):
        """
        初始化處理器
        
        Args:
            employee_start_times: 員工起算時間字典，格式 {考勤號碼: (小時, 分鐘)}
                                 預設所有員工為 (8, 0)
        """
        self.employee_start_times = employee_start_times or {}
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """根據關鍵字尋找欄位"""
        for col in df.columns:
            for keyword in keywords:
                if keyword in col:
                    return col
        return None
    
    def process_csv(self, csv_content: str) -> pd.DataFrame:
        """
        處理 CSV 內容
        
        Args:
            csv_content: CSV 文字內容或檔案路徑
        
        Returns:
            處理後的 DataFrame
        """
        try:
            # 嘗試讀取 CSV
            import os
            if isinstance(csv_content, str) and (csv_content.startswith("/") or os.path.exists(csv_content)):
                # 嘗試多種編碼
                encodings = ['utf-8', 'big5', 'gb2312', 'latin-1', 'cp1252']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(csv_content, encoding=encoding)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                if df is None:
                    raise ValueError("無法以任何編碼讀取 CSV 檔案")
            else:
                from io import StringIO
                df = pd.read_csv(StringIO(csv_content))
        except Exception as e:
            raise ValueError(f"無法讀取 CSV：{str(e)}")
        
        # 標準化欄位名稱
        df.columns = df.columns.str.strip()
        
        # 建立欄位映射字典
        column_mapping = {}
        
        # 尋找姓名欄位
        name_col = self._find_column(df, ["姓名", "名字", "name"])
        if not name_col:
            raise ValueError("缺少姓名欄位")
        column_mapping[name_col] = "姓名"
        
        # 尋找考勤號碼欄位
        emp_id_col = self._find_column(df, ["考勤", "號碼", "id", "員工", "工號"])
        if not emp_id_col:
            raise ValueError("缺少考勤號碼欄位")
        column_mapping[emp_id_col] = "考勤號碼"
        
        # 尋找日期時間欄位
        datetime_col = self._find_column(df, ["日期時間", "時間", "datetime", "date"])
        if not datetime_col:
            raise ValueError("缺少日期時間欄位")
        column_mapping[datetime_col] = "日期時間"
        
        # 尋找簽到/簽退欄位
        check_col = self._find_column(df, ["簽", "check", "status"])
        if not check_col:
            raise ValueError("缺少簽到/退欄位")
        column_mapping[check_col] = "簽到/退"
        
        # 應用欄位映射
        df.rename(columns=column_mapping, inplace=True)
        
        # 分組處理
        results = []
        grouped = df.groupby(["姓名", "考勤號碼"])
        
        for (name, emp_id), group in grouped:
            # 提取日期（從日期時間欄位）
            group["日期"] = group["日期時間"].str.extract(r'(\d+/\d+/\d+)')[0]
            
            for date_str, date_group in group.groupby("日期"):
                if pd.isna(date_str):
                    continue
                
                # 解析日期
                try:
                    date = datetime.strptime(date_str, "%Y/%m/%d").date()
                except ValueError:
                    continue
                
                # 建立打卡記錄
                records = []
                for _, row in date_group.iterrows():
                    record = AttendanceRecord(
                        name=name,
                        emp_id=emp_id,
                        datetime_str=row["日期時間"],
                        check_type=row.get("簽到/退", "")
                    )
                    if record.datetime:
                        records.append(record)
                
                if not records:
                    continue
                
                # 建立日出勤記錄
                start_hour, start_minute = self.employee_start_times.get(
                    str(emp_id), (8, 0)
                )
                
                daily = DailyAttendance(
                    name=name,
                    emp_id=emp_id,
                    date=datetime.combine(date, datetime.min.time()),
                    records=records,
                    start_time_hour=start_hour,
                    start_time_minute=start_minute
                )
                
                results.append(daily.to_dict())
        
        # 轉換為 DataFrame
        if not results:
            raise ValueError("沒有可處理的記錄")
        
        result_df = pd.DataFrame(results)
        
        # 轉換日期為 datetime 以便正確排序
        result_df["日期"] = pd.to_datetime(result_df["日期"], format="%Y/%m/%d")
        
        # 按日期和姓名排序
        result_df = result_df.sort_values(["日期", "姓名"], ascending=[True, True]).reset_index(drop=True)
        
        # 轉換日期回字串格式
        result_df["日期"] = result_df["日期"].dt.strftime("%Y/%m/%d")
        
        # 確保欄位順序
        column_order = [
            "日期", "姓名", "考勤號碼", "上班時間", "下班時間",
            "休息開始", "休息結束", "休息分鐘數", "實際工時", "加班時數", "備註"
        ]
        
        return result_df[column_order]
    
    def export_to_excel(self, df: pd.DataFrame, output_path: str):
        """
        匯出為 Excel 檔案
        
        Args:
            df: 結果 DataFrame
            output_path: 輸出檔案路徑
        """
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
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
