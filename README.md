# 🚛 LINE Bot ค้นหาหัวเก๋ง

Bot สำหรับค้นหารายการหัวเก๋งจาก Google Sheets ผ่าน LINE

---

## 📋 ขั้นตอนติดตั้ง

### ขั้นตอนที่ 1: สร้าง LINE Bot

1. ไปที่ https://developers.line.biz
2. สร้าง Provider → สร้าง Channel ประเภท **Messaging API**
3. เก็บ **Channel Secret** และ **Channel Access Token** (ออก Token แบบ long-lived)
4. ในแท็บ Messaging API → เปิด **"Use webhook"**

---

### ขั้นตอนที่ 2: ตั้งค่า Google Sheets

#### 2.1 Copy ข้อมูลจาก Excel ไป Google Sheets
- เปิด Google Sheets ใหม่
- Copy ข้อมูลจากไฟล์ Excel วางลงไป
- ตั้งชื่อ Sheet ว่า **หัวเก๋ง3-69** (หรือแก้ใน .env)

#### 2.2 สร้าง Google Service Account
1. ไปที่ https://console.cloud.google.com
2. สร้างโปรเจกต์ใหม่
3. เปิดใช้ **Google Sheets API**
4. ไปที่ IAM & Admin → Service Accounts → สร้าง Service Account
5. ดาวน์โหลด credentials JSON → ตั้งชื่อไฟล์ว่า **credentials.json**
6. วางไฟล์ credentials.json ไว้ในโฟลเดอร์เดียวกับ app.py

#### 2.3 แชร์ Google Sheet ให้ Service Account
- ใน Google Sheets กด Share
- ใส่ email ของ Service Account (ดูได้ในไฟล์ credentials.json หัวข้อ client_email)
- ให้สิทธิ์ **Viewer**

---

### ขั้นตอนที่ 3: ตั้งค่า Environment Variables

```bash
cp .env.example .env
```

แก้ไขไฟล์ .env:
```
LINE_CHANNEL_SECRET=xxxxxxxxxxxx
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxx
SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
SHEET_NAME=หัวเก๋ง3-69
```

> **SPREADSHEET_ID** คือ ID ที่อยู่ใน URL ของ Google Sheets
> เช่น: https://docs.google.com/spreadsheets/d/**1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms**/edit

---

### ขั้นตอนที่ 4: Deploy บน Railway (แนะนำ ฟรี)

1. สมัคร https://railway.app (ล็อกอินด้วย GitHub)
2. กด **New Project → Deploy from GitHub repo**
3. อัปโหลด code ขึ้น GitHub ก่อน หรือใช้ Railway CLI
4. ตั้งค่า Environment Variables ใน Railway Dashboard
5. Railway จะสร้าง URL ให้อัตโนมัติ เช่น `https://yourapp.railway.app`

#### หรือ Deploy บน Render (ฟรี)
1. สมัคร https://render.com
2. New → Web Service → เชื่อม GitHub repo
3. ตั้งค่า:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. เพิ่ม Environment Variables

---

### ขั้นตอนที่ 5: ตั้งค่า Webhook URL

1. เอา URL จาก Railway/Render เช่น `https://yourapp.railway.app`
2. ไปที่ LINE Developers Console → Messaging API
3. ตั้ง Webhook URL: `https://yourapp.railway.app/webhook`
4. กด **Verify** → ต้องได้ Success

---

## 💬 วิธีใช้งาน Bot

| พิมพ์ | ผลลัพธ์ |
|-------|---------|
| `SK45` | แสดงรายการลำดับ SK45 ทั้งหมด |
| `VIP` | แสดงรายการ VIP ทั้งหมด |
| `HINO S700` | แสดงหัวเก๋ง HINO S700 ทั้งหมด |
| `ISUZU GIGA` | แสดงหัวเก๋ง ISUZU GIGA ทั้งหมด |
| `FUSO` | แสดง MITSUBISHI FUSO ทั้งหมด |
| `help` | แสดงวิธีใช้งาน |

---

## 📁 โครงสร้างไฟล์

```
linebot/
├── app.py              # LINE Webhook หลัก
├── sheets.py           # ดึงข้อมูลจาก Google Sheets
├── credentials.json    # Google Service Account (อย่า commit ขึ้น GitHub!)
├── requirements.txt    # Python packages
├── .env                # Environment variables (อย่า commit!)
├── .env.example        # ตัวอย่าง .env
└── README.md
```

> ⚠️ **สำคัญ:** อย่า commit ไฟล์ credentials.json และ .env ขึ้น GitHub เด็ดขาด
> ให้สร้าง .gitignore และเพิ่ม:
> ```
> credentials.json
> .env
> ```

---

## 🛠️ รันในเครื่องทดสอบ

```bash
pip install -r requirements.txt
python app.py
```

ใช้ [ngrok](https://ngrok.com) สร้าง public URL สำหรับทดสอบ:
```bash
ngrok http 5000
```
แล้วนำ URL จาก ngrok ไปตั้งใน LINE Webhook
