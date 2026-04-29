import os
import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")

# Column indices (0-based)
COL_DATE     = 0  # A: ซื้อเข้า
COL_NAME     = 1  # B: หัวเก๋ง
COL_ORDER    = 2  # C: รหัส
COL_SUPPLIER = 3  # D: ผู้จำหน่าย/Lot
COL_ENGINE   = 4  # E: เครื่องยนต์
COL_TYPE     = 5  # F: ลักษณะ
COL_COST     = 6  # G: ราคาทุน
COL_COST_PAINT = 7  # H: ราคาทุน(ทำสีแล้ว)
COL_NOTE     = 8  # I: หมายเหตุ


def get_service():
    import json
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()


def get_all_rows():
    sheet = get_service()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:I2000"
    ).execute()
    return result.get("values", [])


def safe_get(row, index, default=""):
    try:
        val = row[index]
        return val.strip() if isinstance(val, str) else str(val)
    except IndexError:
        return default


def extract_number(order_val):
    try:
        val = order_val.strip()
        if "." in val:
            decimal_part = val.split(".")[1]
            return decimal_part.lstrip("0") or "0"
        return re.sub(r"\D", "", val)
    except Exception:
        return ""


def format_vip(order_val):
    num = extract_number(order_val)
    if num:
        return f"VIP{num}"
    return order_val


def fmt_price(p):
    if not p:
        return "-"
    try:
        return f"{int(float(p)):,} บาท"
    except ValueError:
        return p


def format_item(row):
    order_raw = safe_get(row, COL_ORDER)
    return {
        "date":          safe_get(row, COL_DATE) or "-",
        "name":          safe_get(row, COL_NAME),
        "order_num":     extract_number(order_raw),
        "order_display": format_vip(order_raw),
        "supplier":      safe_get(row, COL_SUPPLIER) or "-",
        "engine":        safe_get(row, COL_ENGINE) or "-",
        "type":          safe_get(row, COL_TYPE) or "-",
        "cost":          fmt_price(safe_get(row, COL_COST)),
        "cost_paint":    fmt_price(safe_get(row, COL_COST_PAINT)),
        "note":          safe_get(row, COL_NOTE) or "-",
        "sold":          "ขาย" in safe_get(row, COL_NOTE),
    }


def search_by_order(keyword):
    rows = get_all_rows()
    keyword = keyword.strip().lstrip("0")
    results = []

    for row in rows:
        if len(row) < 3:
            continue
        name_val = safe_get(row, COL_NAME)
        if not name_val or name_val in ("หัวเก๋ง", "B"):
            continue
        order_raw = safe_get(row, COL_ORDER)
        order_num = extract_number(order_raw)
        if order_num == keyword:
            results.append(format_item(row))

    return results


def build_message(results, keyword):
    if not results:
        return (
            f'ไม่พบข้อมูล VIP{keyword}\n\n'
            f'กรุณาตรวจสอบตัวเลขแล้วลองใหม่\n'
            f'หรือพิมพ์ help เพื่อดูวิธีใช้'
        )

    total = len(results)
    lines = []

    for i, item in enumerate(results, 1):
        short_name = item["name"].replace("หัวเก๋ง ", "").strip()
        status = "🔴 ขายแล้ว" if item["sold"] else "🟢 มีในสต็อก"

        block = "\n".join([
            f'{item["order_display"]} 🚛 {short_name}',
            "─" * 28,
            f'📅 {item["date"]}  |  👤 {item["supplier"]}',
            "",
            f'⚙️ {item["engine"]}',
            f'ลักษณะ: {item["type"]}',
            "",
            f'💰 ราคาทุน: {item["cost"]}',
            f'🎨 ราคา+ทำสี: {item["cost_paint"]}',
            "",
            f'📋 {item["note"]}',
            "",
            status,
        ])

        if total > 1:
            block = f"[{i}/{total}]\n" + block

        lines.append(block)

    return ("\n" + "─" * 28 + "\n").join(lines)
