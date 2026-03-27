import sqlite3
from datetime import datetime
import os

# ตั้งค่าพาธไฟล์ฐานข้อมูล
DB_PATH = os.path.join(os.path.dirname(__file__), 'trading_db.sqlite')

def init_db():
    """สร้างตารางที่จำเป็นถ้ายังไม่มี"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. ตารางเก็บ "ความคิด" และการเปิดไม้
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            decision TEXT,
            strategy TEXT,
            lot REAL,
            reason TEXT,
            price REAL,
            status TEXT DEFAULT 'open' -- 'open' หรือ 'closed'
        )
    ''')
    
    # 2. ตารางเก็บ "ผลลัพธ์" หลังปิดไม้ (กำไร/ขาดทุน จริงจาก MT5)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER,
            close_timestamp TEXT,
            profit REAL,
            pips REAL,
            FOREIGN KEY (trade_id) REFERENCES trade_logs(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def log_trade_decision(decision, strategy, lot, reason, price):
    """บันทึกเหตุผลที่ AI เลือกเทรด พร้อมเวลาที่ละเอียดขึ้น"""
    if decision.lower() == 'wait':
        return None
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # เพิ่ม %f เพื่อเก็บ Microseconds กันการซ้ำในวินาทีเดียวกัน
    precise_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] 
    
    cursor.execute('''
        INSERT INTO trade_logs (timestamp, decision, strategy, lot, reason, price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (precise_time, decision, strategy, lot, reason, price, 'open'))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def log_trade_result(trade_id, profit, pips=0):
    """บันทึกกำไร/ขาดทุนจริงหลังจากปิดไม้"""
    if trade_id is None:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. บันทึกผลลัพธ์ลง trade_results
    cursor.execute('''
        INSERT INTO trade_results (trade_id, close_timestamp, profit, pips)
        VALUES (?, ?, ?, ?)
    ''', (trade_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), profit, pips))
    
    # 2. อัปเดตสถานะใน trade_logs ให้เป็น closed
    cursor.execute('UPDATE trade_logs SET status = "closed" WHERE id = ?', (trade_id,))
    
    conn.commit()
    conn.close()
    print(f"📁 [DB]: Updated Profit for Trade ID {trade_id}: ${profit}")

def get_recent_history(limit=5):
    """ดึงประวัติล่าสุดมาให้ AI อ่าน (The Learning Context)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # ดึงข้อมูลจากทั้งสองตารางมาให้ AI วิเคราะห์ผลแพ้ชนะในอดีตด้วย
    cursor.execute('''
        SELECT l.decision, l.strategy, l.reason, l.status, r.profit
        FROM trade_logs l
        LEFT JOIN trade_results r ON l.id = r.trade_id
        ORDER BY l.id DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_full_trade_history(limit=50):
    """ดึงประวัติทั้งหมดพร้อมกำไรมาโชว์ในหน้า Frontend"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # ใช้ LEFT JOIN เพื่อเอาค่า Profit มาโชว์ในตารางเดียว
    cursor.execute('''
        SELECT 
            l.id, l.timestamp, l.decision, l.strategy, l.lot, 
            l.price, l.status, l.reason, r.profit
        FROM trade_logs l
        LEFT JOIN trade_results r ON l.id = r.trade_id
        ORDER BY l.id DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# รันเพื่อสร้างไฟล์ DB ทันทีที่เรียกใช้
init_db()