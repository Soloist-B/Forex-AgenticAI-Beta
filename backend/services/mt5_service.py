import MetaTrader5 as mt5
import pandas as pd
import time

# --- 1. ฟังก์ชันเชื่อมต่อ ---
def connect_mt5():
    if not mt5.initialize():
        print("❌ initialize() failed, error code =", mt5.last_error())
        return False
    return True

# --- 2. ฟังก์ชันดึงราคา ---
def get_gold_price(symbol="XAUUSD.iux"):
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    return {"bid": tick.bid, "ask": tick.ask}

# --- 3. ฟังก์ชันเช็คสถานะออเดอร์ ---
def has_open_positions(symbol="XAUUSD.iux"):
    positions = mt5.positions_get(symbol=symbol)
    return len(positions) > 0 if positions is not None else False

# --- 4. ฟังก์ชันดึง Indicator (ปรับปรุงเพื่อ Multi-TF) ---
def get_indicators(symbol="XAUUSD.iux", timeframe=mt5.TIMEFRAME_M5, n=600):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) < 50:
        return {"rsi": 50.0, "ema_50": 0.0, "trend": "SIDEWAY", "high": 0.0, "low": 0.0, "close": 0.0}
    
    df = pd.DataFrame(rates)
    
    # คำนวณ RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # คำนวณ EMA 50
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    last_row = df.iloc[-1]
    return {
        "rsi": round(float(last_row['RSI']), 2) if not pd.isna(last_row['RSI']) else 50.0,
        "ema_50": round(float(last_row['EMA_50']), 2),
        "trend": "UP" if last_row['close'] > last_row['EMA_50'] else "DOWN",
        "high": round(float(df['high'].max()), 2), # แนวต้านในช่วง n แท่ง
        "low": round(float(df['low'].min()), 2),   # แนวรับในช่วง n แท่ง
        "close": round(float(last_row['close']), 2)
    }

# --- 5. ฟังก์ชันส่งคำสั่งซื้อขาย (Open) ---
# บอสครับ ผมเพิ่ม tp_dist และ sl_dist มารับค่าจากสภา AI แล้วนะครับ (Default ที่ 500 ถ้าสภาไม่ส่งมา)
def place_order(action, lot=0.01, symbol="XAUUSD.iux", tp_dist=500, sl_dist=500):
    if not mt5.initialize():
        connect_mt5()
        
    tick = get_gold_price(symbol)
    symbol_info = mt5.symbol_info(symbol)
    if tick is None or symbol_info is None: return None

    # คำนวณระยะตามที่ AI สั่งมา
    if action.lower() == 'buy':
        price = tick['ask']
        sl = price - (sl_dist * symbol_info.point)
        tp = price + (tp_dist * symbol_info.point)
        order_type = mt5.ORDER_TYPE_BUY
    else:
        price = tick['bid']
        sl = price + (sl_dist * symbol_info.point)
        tp = price - (tp_dist * symbol_info.point)
        order_type = mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": order_type,
        "price": price,
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "magic": 123456,
        "comment": "AI Council v3.5",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK, 
    }
    
    result = mt5.order_send(request)
    
    # Logic เดิมที่บอสชอบ: ถ้า FOK พลาด (10030) ให้ลอง RETURN ทันที
    if result.retcode == 10030:
        request["type_filling"] = mt5.ORDER_FILLING_RETURN
        result = mt5.order_send(request)
        
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Order failed: {result.comment} (code: {result.retcode})")
        
    return result

# --- 6. ฟังก์ชันสั่งปิดออเดอร์ (Close) ---
def close_position(symbol="XAUUSD.iux"):
    positions = mt5.positions_get(symbol=symbol)
    if not positions: return None

    last_result = None
    for p in positions:
        tick = get_gold_price(symbol)
        order_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick['bid'] if p.type == mt5.ORDER_TYPE_BUY else tick['ask']

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": p.volume,
            "type": order_type,
            "position": p.ticket,
            "price": price,
            "magic": 123456,
            "comment": "AI Council Exit",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        last_result = mt5.order_send(request)
        if last_result.retcode == 10030:
            request["type_filling"] = mt5.ORDER_FILLING_RETURN
            last_result = mt5.order_send(request)
            
    return last_result