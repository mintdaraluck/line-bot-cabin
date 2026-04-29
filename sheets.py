import os
import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "หัวเก๋ง3-69")

# Column indices (0-based) จาก Excel ต้นฉบับ
COL_DATE = 0       # ว.ด.ป.
COL_NAME = 1       # หัวเก๋ง (ยี่ห้อ/รุ่น)
COL_ORDER = 2      # ลำดับ (VIP/SK/GH ฯลฯ)
COL_SUPPLIER = 3   # ผู้จำหน่าย
COL_ENGINE = 4     # เครื่องยนต์
COL_NOTE1 = 5      # หมายเหตุ (หัวติดเครื่อง ฯลฯ)
COL_COST = 6       # ราคาทุน
COL_COST_PAINT = 7 # ราคาทุน+ทำสี
COL_NOTE2 = 10     # หมายเหตุท้าย (ขาย/กำลังทำสี ฯลฯ)


def get_service():
    import json
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        # อ่านจาก Environment Variable (Railway)
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # อ่านจากไฟล์ (local)
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()


def get_all_rows():
    """ดึงข้อมูลทั้งหมดจาก Google Sheets"""
    sheet = get_service()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:K2000"
    ).execute()
    return result.get("values", [])


def safe_get(row, index, default=""):
    try:
        val = row[index]
        return val.strip() if isinstance(val, str) else str(val)
    except IndexError:
        return default



def extract_number(order_val):
    """ดึงตัวเลขออกจาก column C เช่น 0.1788 → '1788'"""
    # column C เก็บค่าเป็น decimal เช่น 0.1788
    # ตัดทศนิยม 0. ออก แล้วเอาเฉพาะตัวเลข 4 ตัวหลัง
    try:
        # กรณีเป็นตัวเลข float เช่น 0.1788
        val = order_val.strip()
        if "." in val:
            decimal_part = val.split(".")[1]  # เอาส่วน 1788
            return decimal_part.lstrip("0") or "0"
        # กรณีเป็นตัวเลขล้วน
        return re.sub(r"\D", "", val)
    except Exception:
        return ""


def format_vip(order_val):
    """แปลง column C เป็น VIP1788"""
    num = extract_number(order_val)
    if num:
        return f"VIP{num}"
    return order_val  # fallback กรณีรูปแบบแปลก


def format_item(row):
    """แปลงแถวเป็น dict ที่อ่านง่าย"""
    name = safe_get(row, COL_NAME)
    order_raw = safe_get(row, COL_ORDER)
    supplier = safe_get(row, COL_SUPPLIER)
    engine = safe_get(row, COL_ENGINE)
    note1 = safe_get(row, COL_NOTE1)
    cost = safe_get(row, COL_COST)
    cost_paint = safe_get(row, COL_COST_PAINT)
    note2 = safe_get(row, COL_NOTE2)

    def fmt_price(p):
        if not p:
            return "-"
        try:
            return f"{int(float(p)):,} บาท"
        except ValueError:
            return p

    return {
        "name": name,
        "order_raw": order_raw,
        "order_num": extract_number(order_raw),       # "1788"
        "order_display": format_vip(order_raw),       # "VIP1788"
        "supplier": supplier,
        "engine": engine or "-",
        "note1": note1 or "-",
        "cost": fmt_price(cost),
        "cost_paint": fmt_price(cost_paint),
        "note2": note2,
        "sold": "ขาย" in note2,
    }


def search_by_order(keyword):
    """ค้นหาด้วยตัวเลข 4 หลักใน column C เช่น 1788"""
    rows = get_all_rows()
    keyword = keyword.strip().lstrip("0")  # ตัด 0 นำหน้าออก เผื่อผู้ใช้พิมพ์ 01788
    results = []

    for row in rows:
        if len(row) < 3:
            continue
        name_val = safe_get(row, COL_NAME)
        if not name_val or name_val == "หัวเก๋ง":  # กรอง header
            continue

        order_raw = safe_get(row, COL_ORDER)
        order_num = extract_number(order_raw)  # ดึงเฉพาะตัวเลข

        if order_num == keyword:
            results.append(format_item(row))

    return results


def build_message(results, keyword):
    """สร้างข้อความตอบกลับสำหรับ LINE"""
    if not results:
        return f'🔍 ไม่พบข้อมูล VIP{keyword}\n\nกรุณาตรวจสอบตัวเลขแล้วลองใหม่\nหรือพิมพ์ help เพื่อดูวิธีใช้'

    # จำกัด 5 รายการต่อการค้นหา
    MAX_SHOW = 5
    total = len(results)
    show = results[:MAX_SHOW]

    lines = [f'🔍 ผลการค้นหา VIP{keyword} พบ {total} รายการ\n{"─" * 28}']

    for i, item in enumerate(show, 1):
        status = "🔴 ขายแล้ว" if item["sold"] else "🟢 มีในสต็อก"
        block = [
            f'\n#{i} {item["name"]}',
            f'📌 ลำดับ: {item["order_display"]}',
            f'👤 ผู้จำหน่าย: {item["supplier"] or "-"}',
            f'⚙️ เครื่องยนต์: {item["engine"]}',
            f'📝 หมายเหตุ: {item["note1"]}',
            f'💰 ราคาทุน: {item["cost"]}',
            f'🎨 ราคา+ทำสี: {item["cost_paint"]}',
            f'{status}',
        ]
        if item["note2"]:
            block.append(f'📋 {item["note2"]}')
        lines.append("\n".join(block))

    if total > MAX_SHOW:
        lines.append(f'\n{"─" * 28}\n⚠️ แสดง {MAX_SHOW}/{total} รายการ\nกรุณาระบุรหัสให้ชัดเจนขึ้น')

    return "\n".join(lines)
