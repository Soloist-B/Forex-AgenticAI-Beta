import ollama
import json
import MetaTrader5 as mt5
from services.mt5_service import get_gold_price, get_indicators
from engine.db_manager import log_trade_decision, get_recent_history

# ตัวแปรรับคำสั่งโดยตรงจากบอส
current_user_instruction = "วิเคราะห์ตามความเหมาะสมทางเทคนิค"

def set_instruction(text):
    global current_user_instruction
    current_user_instruction = text
    print(f"📥 [Instruction Updated]: {current_user_instruction}")

class TradingAgent:
    def __init__(self, model_name='llama3'):
        self.model_name = model_name
        self.agents = {
            "Scalper": "เน้นเก็บกำไรระยะสั้น ดู RSI M5 เป็นหลัก ชอบความไว วาง TP/SL แคบเพื่อจบเกมไว",
            "Trend_Follower": "เน้นดู EMA 50 และเทรนด์จาก H1 วาง TP ให้กว้างกว่า SL เพื่อเอา Risk:Reward ที่คุ้มค่า",
            "Risk_Manager": "คุมความเสี่ยงตาม Balance ห้ามออก Lot เกินตัว และต้องอนุมัติระยะ SL ที่ไม่ทำให้พอร์ตเสียหายหนัก"
        }
        print(f"🤖 AI Council v3.9.6 (Dynamic Trailing) Initialized")

    def _safe_json_decode(self, content):
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            return json.loads(content[start:end])
        except:
            return None

    def analyze_market(self):
        """ประชุมสภา AI เพื่อเปิดไม้และกำหนด TP/SL/TS เอง"""
        global current_user_instruction
        try:
            price_data = get_gold_price()
            m5_indicators = get_indicators(timeframe=mt5.TIMEFRAME_M5)
            h1_indicators = get_indicators(timeframe=mt5.TIMEFRAME_H1)
            
            account_info = mt5.account_info()
            balance = account_info.balance if account_info else 0
            
            past_trades = get_recent_history(25)
            history_context = "\n".join([
                f"- {t[0].upper()} ({t[1]}) ผลลัพธ์: {'กำไร' if (t[4] or 0) > 0 else 'ขาดทุน'} ${t[4] if t[4] else 0}" 
                for t in past_trades
            ])

            prompt = f"""
            คุณคือ 'ประธานสภา AI' นำการประชุมสภา 3 ท่านเพื่อเทรดทองคำ (XAUUSD):
            1. Scalper: {self.agents['Scalper']}
            2. Trend Follower: {self.agents['Trend_Follower']}
            3. Risk Manager: {self.agents['Risk_Manager']}

            [สถานะพอร์ต]: Balance ${balance:.2f}
            [คำสั่งบอส]: {current_user_instruction}
            
            [ข้อมูลตลาดปัจจุบัน]:
            - ราคาปัจจุบัน: {price_data['bid']}
            - M5 (Entry): RSI {m5_indicators['rsi']}, Trend {m5_indicators['trend']}
            - H1 (Master Trend): Trend {h1_indicators['trend']} (EMA50)

            [ประวัติล่าสุด]: {history_context if history_context else "ไม่มีข้อมูล"}

            ภารกิจ:
            1. ตัดสินใจว่าจะ Buy, Sell หรือ Wait
            2. ถ้าเข้าเทรด ให้กำหนด Lot (0.01 - 0.05) 
            3. กำหนดระยะ TP และ SL เป็นจำนวน 'จุด (Points)'
            4. **กำหนดระยะ Trailing Stop (ts_distance) เป็นจำนวนจุด (200-600) เพื่อรันกำไร**

            ตอบเป็น JSON เท่านั้น:
            {{
                "decision": "buy" | "sell" | "wait",
                "strategy": "Scalping" | "Swing",
                "lot": 0.01,
                "tp_distance": 500,
                "sl_distance": 300,
                "ts_distance": 400,
                "debate_summary": "สรุปการถกเถียง",
                "reason": "เหตุผลสุดท้าย"
            }}
            """
            
            response = ollama.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
            data = self._safe_json_decode(response['message']['content'])
            
            if not data:
                return {"decision": "wait", "lot": 0.01, "tp_distance": 500, "sl_distance": 500, "ts_distance": 400}, "JSON Error"
            
            final_reason = f"[{data.get('strategy')}] TS:{data.get('ts_distance')} | {data.get('debate_summary')}"
            return data, final_reason
        
        except Exception as e:
            print(f"❌ analyze_market Error: {e}")
            return {"decision": "wait", "lot": 0.01}, str(e)

    def check_to_close(self, current_trade_info):
        """ประชุมสภาเพื่อพิจารณาปิดไม้"""
        try:
            price_data = get_gold_price()
            m5_indicators = get_indicators(timeframe=mt5.TIMEFRAME_M5)
            trade_type = current_trade_info['type']
            profit = current_trade_info['profit']

            prompt = f"""
            [ประชุมด่วน: พิจารณาถือครองออเดอร์]
            ออเดอร์: {trade_type} XAUUSD | กำไรปัจจุบัน: ${profit}
            ตลาด (M5): RSI {m5_indicators['rsi']}, Trend {m5_indicators['trend']}

            ภารกิจสภา:
            1. เรามีระบบ Trailing Stop คอยคุมอยู่แล้ว ห้ามสั่งปิดเพียงเพราะกลัว
            2. หากสถานการณ์ยังปกติ ให้เลือก "hold" เพื่อรันกำไร
            3. สั่งปิด (close) เฉพาะเมื่อสภาเห็นสัญญาณกลับตัวที่รุนแรงจริงๆ

            ตอบเป็น JSON เท่านั้น:
            {{
                "action": "close" | "hold",
                "reason": "อธิบายสั้นๆ"
            }}
            """
            response = ollama.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
            data = self._safe_json_decode(response['message']['content'])
            
            if data and data.get('action') == 'close':
                return True, data.get('reason')
            
            return False, "Hold"
        except:
            return False, "Error"

gold_agent = TradingAgent()