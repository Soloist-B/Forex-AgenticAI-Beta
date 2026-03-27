import MetaTrader5 as mt5
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
from contextlib import asynccontextmanager
import datetime as dt

# --- IMPORT ---
try:
    from services.mt5_service import (
        connect_mt5, get_gold_price, place_order, 
        has_open_positions, get_indicators, close_position, modify_sl
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
TS_STEP_POINTS = 50 

async def auto_trading_loop():
    global current_db_id, is_processing, app_ready
    
    while not app_ready:
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
                print(f"📦 [HOLDING] พบไม้ค้าง: {('BUY' if p.type == 0 else 'SELL')} | Profit: {round(p.profit, 2)} USD | SL: {p.sl}")
                
                # Sync ID
                if current_db_id is None:
                    print("🔍 [SYNC] พยายามกู้คืน DB_ID...")
                    history = get_full_trade_history(5)
                    for log in history:
                        if log['status'] == 'open':
                            current_db_id = log['id']
                            print(f"✅ [SYNC] พบ ID: {current_db_id}")
                            break

                # --- TRAILING STOP LOGIC ---
                symbol_info = mt5.symbol_info(p.symbol)
                tick = get_gold_price(p.symbol)
                
                my_ts_dist = 400 
                full_history = get_full_trade_history(10)
                for item in full_history:
                    if item['id'] == current_db_id:
                        my_ts_dist = item.get('ts_distance', 400)
                        break

                if tick and symbol_info:
                    point = symbol_info.point
                    if p.type == 0: # BUY
                        new_sl = round(tick['bid'] - (my_ts_dist * point), 2)
                        if new_sl > p.sl + (TS_STEP_POINTS * point):
                            modify_sl(p.ticket, new_sl, p.symbol)
                            print(f"📈 [TS-UP] ขยับ SL ตามราคาไปที่: {new_sl} (Dist: {my_ts_dist})")
                    elif p.type == 1: # SELL
                        new_sl = round(tick['ask'] + (my_ts_dist * point), 2)
                        if p.sl == 0 or new_sl < p.sl - (TS_STEP_POINTS * point):
                            modify_sl(p.ticket, new_sl, p.symbol)
                            print(f"📉 [TS-DOWN] ขยับ SL ตามราคาไปที่: {new_sl} (Dist: {my_ts_dist})")
                
                # --- COUNCIL EXIT ANALYSIS ---
                current_info = {"type": ("BUY" if p.type == 0 else "SELL"), "price": p.price_open, "profit": round(p.profit, 2), "symbol": "XAUUSD.iux"}
                print("🧠 [COUNCIL] กำลังวิเคราะห์จังหวะ Exit...")
                should_close, exit_reason = gold_agent.check_to_close(current_info)
                
                if should_close:
                    is_processing = True 
                    print(f"🚨 [EXIT SIGNAL] สั่งปิดออเดอร์! เหตุผล: {exit_reason}")
                    result = close_position("XAUUSD.iux")
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"💰 [CLOSED] ปิดสำเร็จ! กำไร: {p.profit} USD")
                        log_trade_result(current_db_id, p.profit)
                        current_db_id = None
                    is_processing = False 
                else:
                    print(f"💎 [HOLD] Council มติให้ถือต่อ (Profit: {round(p.profit, 2)})")
                
                await asyncio.sleep(15)
            
            # --- STEP 2: ANALYZE NEW TRADE ---
            else:
                if current_db_id is not None:
                    print(f"⚠️ [SYNC] ไม้ ID {current_db_id} หายไป (ชน SL/TP)")
                    from_date = dt.datetime.now() - dt.timedelta(minutes=15)
                    deals = mt5.history_deals_get(from_date, dt.datetime.now())
                    actual_profit = 0.0
                    if deals:
                        for deal in reversed(deals):
                            if deal.symbol == "XAUUSD.iux" and deal.entry == 1:
                                actual_profit = deal.profit
                                break
                    log_trade_result(current_db_id, actual_profit)
                    current_db_id = None

                print("🔭 [SCAN] พอร์ตว่าง... เริ่มประชุมสภา AI")
                is_processing = True 
                
                indicators = get_indicators()
                print(f"📊 [MARKET DATA] Indicators: {indicators}")
                
                decision_data, reason = gold_agent.analyze_market()
                decision = decision_data.get('decision', 'wait').lower()
                print(f"🧐 [COUNCIL REASONING] {reason}")

                if decision in ['buy', 'sell']:
                    # Final Guard
                    if mt5.positions_get(symbol="XAUUSD.iux"):
                        print("🚫 [PROTECT] พบไม้เปิดอยู่แล้ว ยกเลิก")
                        is_processing = False
                        continue

                    lot = float(decision_data.get('lot', 0.01))
                    ts_dist = int(decision_data.get('ts_distance', 400))
                    print(f"🔥 [EXECUTE] มติเอกฉันท์: {decision.upper()} | Lot: {lot} | TS: {ts_dist}")
                    
                    res = place_order(decision, lot=lot, tp_dist=int(decision_data.get('tp_distance', 500)), sl_dist=int(decision_data.get('sl_distance', 300)))
                    
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        price_now = get_gold_price()['bid']
                        current_db_id = log_trade_decision(decision, decision_data.get('strategy'), lot, reason, price_now, ts_distance=ts_dist)
                        print(f"🚀 [SUCCESS] เปิดไม้สำเร็จ! Ledger ID: {current_db_id} ที่ {price_now}")
                else:
                    print("😴 [WAIT] สภามติให้รอดูสถานการณ์")
                
                is_processing = False 
                print("💤 [SLEEP] พัก 60 วินาที...")
                await asyncio.sleep(60)

        except Exception as e:
            print(f"🚨 [LOOP ERROR]: {e}")
            is_processing = False
            await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_ready
    print("🚀 [SYSTEM] Starting Startup...")
    if connect_mt5():
        asyncio.create_task(auto_trading_loop())
    app_ready = True
    yield 
    mt5.shutdown()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/status")
def get_status():
    try:
        price_data = get_gold_price()
        acc = mt5.account_info()
        pos = mt5.positions_get(symbol="XAUUSD.iux")
        current_trade = {"type": ("BUY" if pos[0].type == 0 else "SELL"), "price": pos[0].price_open, "profit": round(pos[0].profit, 2)} if pos else None
        return {
            "price": price_data['bid'], "balance": acc.balance, "equity": acc.equity, 
            "current_trade": current_trade, "indicators": get_indicators(), "status": "AI v3.9.6 Active"
        }
    except: return {"status": "Offline"}

@app.get("/api/history")
def get_history():
    return get_full_trade_history(50)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)