import MetaTrader5 as mt5
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
from contextlib import asynccontextmanager
import datetime as dt

# --- IMPORT ส่วนเดิม ---
try:
    from services.mt5_service import (
        connect_mt5, get_gold_price, place_order, 
        has_open_positions, get_indicators, close_position
    )
    from engine.agent import gold_agent, set_instruction 
    from engine.db_manager import (
        get_full_trade_history, log_trade_decision, log_trade_result
    )
except ImportError as e:
    print(f"❌ [CRITICAL] Import Error: {e}")
    import sys
    sys.exit(1)

# --- GLOBAL STATES ---
current_db_id = None
is_processing = False 
app_ready = False 

async def auto_trading_loop():
    global current_db_id, is_processing, app_ready
    
    while not app_ready:
        print("⏳ [WAIT] รอ FastAPI Startup ให้เสร็จสิ้นก่อนเริ่ม Loop...")
        await asyncio.sleep(1)
        
    print("\n" + "="*50)
    print("🤖 [SYSTEM START] AI Council v3.9.6 Active & Monitoring...")
    print("="*50 + "\n")
    
    while True:
        try:
            if is_processing:
                print("⏳ [BUSY] ระบบกำลังประมวลผลคำสั่งเดิมอยู่... ข้ามรอบนี้")
                await asyncio.sleep(2)
                continue

            if not mt5.initialize():
                print("🔌 [MT5] การเชื่อมต่อหลุด! กำลังพยายาม Reconnect...")
                connect_mt5()

            # --- STEP 1: MONITOR POSITIONS ---
            positions = mt5.positions_get(symbol="XAUUSD.iux")
            
            if positions and len(positions) > 0:
                p = positions[0]
                print(f"📦 [HOLDING] พบไม้ค้างในพอร์ต: {('BUY' if p.type == 0 else 'SELL')} | Profit: {round(p.profit, 2)} USD")
                
                # กู้คืน ID จาก Ledger ถ้าหายไป
                if current_db_id is None:
                    print("🔍 [SYNC] พยายามกู้คืน DB_ID จากประวัติการเทรด...")
                    history = get_full_trade_history(5)
                    for log in history:
                        if log['status'] == 'open':
                            current_db_id = log['id']
                            print(f"✅ [SYNC] พบ ID ที่สอดคล้องกัน: {current_db_id}")
                            break

                current_info = {
                    "type": ("BUY" if p.type == 0 else "SELL"), 
                    "price": p.price_open, 
                    "profit": round(p.profit, 2),
                    "symbol": "XAUUSD.iux"
                }
                
                # ให้ Agent ตัดสินใจว่าจะปิดไหม
                print("🧠 [COUNCIL] กำลังวิเคราะห์จังหวะ Exit...")
                should_close, exit_reason = gold_agent.check_to_close(current_info)
                
                if should_close:
                    is_processing = True 
                    print(f"🚨 [EXIT SIGNAL] สั่งปิดออเดอร์ทันที! เหตุผล: {exit_reason}")
                    result = close_position("XAUUSD.iux")
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"💰 [CLOSED] ปิดสำเร็จ! ผลกำไร: {p.profit} USD")
                        log_trade_result(current_db_id, p.profit)
                        current_db_id = None
                    else:
                        print(f"❌ [ERROR] ปิดออเดอร์ไม่สำเร็จ Retcode: {result.retcode if result else 'No Result'}")
                    is_processing = False 
                else:
                    print(f"💎 [HOLD] Council มติให้ถือต่อ (Profit: {round(p.profit, 2)})")
                
                print("💤 [SLEEP] พัก 10 วินาทีตามรอบ Monitoring...")
                await asyncio.sleep(10)
            
            # --- STEP 2: ANALYZE NEW TRADE ---
            else:
                # Sync Ledger กรณีไม้ปิดไปเอง (SL/TP)
                if current_db_id is not None:
                    print(f"⚠️ [SYNC] ไม้ ID {current_db_id} หายจากพอร์ต (อาจชน SL/TP)")
                    from_date = dt.datetime.now() - dt.timedelta(minutes=15)
                    deals = mt5.history_deals_get(from_date, dt.datetime.now())
                    actual_profit = 0.0
                    if deals:
                        for deal in reversed(deals):
                            if deal.symbol == "XAUUSD.iux" and deal.entry == 1:
                                actual_profit = deal.profit
                                break
                    print(f"📝 [UPDATE] บันทึกผลกำไรลง Ledger: {actual_profit}")
                    log_trade_result(current_db_id, actual_profit)
                    current_db_id = None

                print("🔭 [SCAN] พอร์ตว่าง... เริ่มต้นการประชุม Council เพื่อวิเคราะห์ตลาด")
                is_processing = True 
                
                # รับ Data และคำตัดสิน
                decision_data, reason = gold_agent.analyze_market()
                decision = decision_data.get('decision', 'wait').lower()
                
                print(f"📊 [MARKET DATA] Indicators: {get_indicators()}")
                print(f"🧐 [COUNCIL REASONING] {reason}")

                if decision in ['buy', 'sell']:
                    # Final Guard
                    re_pos = mt5.positions_get(symbol="XAUUSD.iux")
                    if re_pos:
                        print("🚫 [PROTECT] ตลาดเปลี่ยนไวกว่าที่คิด! พบไม้เปิดอยู่แล้ว ยกเลิกคำสั่งซ้ำ")
                        is_processing = False
                        continue

                    lot = float(decision_data.get('lot', 0.01))
                    print(f"🔥 [EXECUTE] มติเป็นเอกฉันท์: {decision.upper()} | Lot: {lot}")
                    
                    res = place_order(
                        decision, 
                        lot=lot, 
                        tp_dist=int(decision_data.get('tp_distance', 500)), 
                        sl_dist=int(decision_data.get('sl_distance', 300))
                    )
                    
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        price_now = get_gold_price()['bid']
                        current_db_id = log_trade_decision(
                            decision, 
                            decision_data.get('strategy', 'Scalper'), 
                            lot, reason, price_now
                        )
                        print(f"🚀 [SUCCESS] เปิดไม้สำเร็จ! Ledger ID: {current_db_id} ที่ราคา {price_now}")
                        await asyncio.sleep(5)
                    else:
                        print(f"❌ [FAILED] การเปิด Order ผิดพลาด: {res.comment if res else 'Unknown Error'}")
                else:
                    print(f"😴 [WAIT] Council มติให้ 'รอดูสถานการณ์' (Wait)")

                is_processing = False 
                print("💤 [SLEEP] พัก 30 วินาทีเพื่อเริ่มประชุมรอบถัดไป...")
                await asyncio.sleep(30)

        except Exception as e:
            print(f"🚨 [LOOP ERROR] เกิดข้อผิดพลาดไม่คาดคิด: {str(e)}")
            is_processing = False
            await asyncio.sleep(10)

# --- 3. LIFESPAN MANAGEMENT ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_ready
    print("🚀 [SYSTEM] กำลังเตรียมการ Startup...")
    if connect_mt5():
        print("✅ [SYSTEM] MT5 เชื่อมต่อสำเร็จ")
        asyncio.create_task(auto_trading_loop())
    
    app_ready = True
    yield 
    print("🛑 [SHUTDOWN] กำลังปิดระบบและตัดการเชื่อมต่อ...")
    mt5.shutdown()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- ENDPOINTS ---
@app.get("/api/status")
def get_status():
    try:
        price_data = get_gold_price()
        acc = mt5.account_info()
        pos = mt5.positions_get(symbol="XAUUSD.iux")
        current_trade = {"type": ("BUY" if pos[0].type == 0 else "SELL"), "price": pos[0].price_open, "profit": round(pos[0].profit, 2)} if pos else None
        return {
            "price": price_data['bid'], 
            "balance": acc.balance, 
            "equity": acc.equity, 
            "profit_total": acc.profit, 
            "current_trade": current_trade, 
            "indicators": get_indicators(), 
            "status": "AI v3.9.6 Active",
            "is_processing": is_processing
        }
    except: return {"status": "Offline"}

@app.get("/api/history")
def get_history():
    return get_full_trade_history(50)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)