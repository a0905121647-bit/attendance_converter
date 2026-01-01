"""
出勤轉檔核心計算模組
負責處理打卡資料的解析、工時計算、休息推估等邏輯
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd


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
        
        # 嘗試多種格式
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%m/%d %H:%M",
            "%m-%d %H:%M",
            "%Y-%m-%d %H:%M 上午",
            "%Y-%m-%d %H:%M 下午",
            "%Y/%m/%d %H:%M 上午",
            "%Y/%m/%d %H:%M 下午",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        # 如果都失敗，嘗試更寬鬆的解析
        try:
            # 移除「上午」「下午」等文字
            cleaned = datetime_str.replace("上午", "").replace("下午", "").strip()
            for fmt in ["%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"]:
                try:
                    return datetime.strptime(cleaned, fmt)
                except ValueError:
                    continue
        except:
            pass
        
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
        
        # 取得上班時間（第一筆在起算時間之後的打卡）
        start_time = datetime.combine(
            self.date.date(),
            datetime.min.time().replace(hour=self.start_time_hour, minute=self.start_time_minute)
        )
        
        # 找第一筆有效打卡（不早於起算時間）
        check_in_candidates = [r for r in valid_records if r.datetime >= start_time]
        if not check_in_candidates:
            # 如果所有打卡都早於起算時間，使用起算時間
            self.check_in_time = start_time
            self.remarks = "所有打卡早於起算時間，使用起算時間"
        else:
            self.check_in_time = check_in_candidates[0].datetime
        
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
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "日期": self.date.strftime("%Y/%m/%d") if self.date else "",
            "姓名": self.name,
            "考勤號碼": self.emp_id,
            "上班時間": self.check_in_time.strftime("%H:%M") if self.check_in_time else "",
            "下班時間": self.check_out_time.strftime("%H:%M") if self.check_out_time else "",
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
                df = pd.read_csv(csv_content)
            else:
                from io import StringIO
                df = pd.read_csv(StringIO(csv_content))
        except Exception as e:
            raise ValueError(f"無法讀取 CSV：{str(e)}")
        
        # 標準化欄位名稱
        df.columns = df.columns.str.strip()
        
        # 驗證必要欄位
        required_cols = ["姓名", "考勤號碼", "日期時間"]
        for col in required_cols:
            if col not in df.columns:
                # 嘗試模糊匹配
                matching = [c for c in df.columns if col in c or c in col]
                if matching:
                    df.rename(columns={matching[0]: col}, inplace=True)
                else:
                    raise ValueError(f"缺少必要欄位：{col}")
        
        # 處理簽到/簽退欄位
        if "簽到/退" not in df.columns:
            matching = [c for c in df.columns if "簽" in c or "check" in c.lower()]
            if matching:
                df.rename(columns={matching[0]: "簽到/退"}, inplace=True)
            else:
                raise ValueError("缺少簽到/退欄位")
        
        # 分組處理
        results = []
        grouped = df.groupby(["姓名", "考勤號碼"])
        
        for (name, emp_id), group in grouped:
            # 按日期分組
            group["日期"] = pd.to_datetime(group["日期時間"], errors="coerce").dt.date
            
            for date, date_group in group.groupby("日期"):
                if pd.isna(date):
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
        result_df = pd.DataFrame(results)
        
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
