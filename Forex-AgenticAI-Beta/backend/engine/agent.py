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
            "Scalper": "เน้นเก็บกำไรระยะสั้น ดู RSI M1 เป็นหลัก ชอบความไว วาง TP/SL แคบเพื่อจบเกมไว",
            "Trend_Follower": "เน้นดู EMA 50 และเทรนด์จาก M15/H1 วาง TP ให้กว้างกว่า SL เพื่อเอา Risk:Reward ที่คุ้มค่า",
            "Risk_Manager": "คุมความเสี่ยงตาม Balance ห้ามออก Lot เกินตัว และต้องอนุมัติระยะ SL ที่ไม่ทำให้พอร์ตเสียหายหนัก"
        }
        print(f"🤖 AI Council v3.9.6 (Multi-TF Sniper) Initialized")

    def _safe_json_decode(self, content):
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            return json.loads(content[start:end])
        except:
            return None

    def analyze_market(self):
        """ประชุมสภา AI: มติเอกฉันท์จาก M1 (Entry), M15 (Structure) และ H1 (Master Trend)"""
        global current_user_instruction
        try:
            # 1. ดึงข้อมูลตลาดแบบ Multi-Timeframe
            price_data = get_gold_price()
            m1_indicators = get_indicators(timeframe=mt5.TIMEFRAME_M1)   # หาจุดเข้า Sniper
            m15_indicators = get_indicators(timeframe=mt5.TIMEFRAME_M15) # ดูแนวรับ-แนวต้านสั้น
            h1_indicators = get_indicators(timeframe=mt5.TIMEFRAME_H1)   # ดูเทรนด์หลัก
            
            account_info = mt5.account_info()
            balance = account_info.balance if account_info else 0
            
            # 2. ดึงประวัติล่าสุด (The Learning Context)
            past_trades = get_recent_history(15)
            history_context = "\n".join([
                f"- {t[0].upper()} ({t[1]}) ผลลัพธ์: {'กำไร' if (t[4] or 0) > 0 else 'ขาดทุน'} ${t[4] if t[4] else 0}" 
                for t in past_trades
            ])

            # 3. เตรียม Debate Prompt สำหรับ 3 Timeframes
            prompt = f"""
            คุณคือ 'ประธานสภา AI' นำการประชุมสภา 3 ท่านเพื่อเทรดทองคำ (XAUUSD):
            1. Scalper: {self.agents['Scalper']} (เน้น RSI และ Price Action ใน M1)
            2. Trend Follower: {self.agents['Trend_Follower']} (เน้น EMA50 ใน M15 และ H1)
            3. Risk Manager: {self.agents['Risk_Manager']} (คุมระยะ SL/TP ให้คุ้มค่า RR)

            [สถานะพอร์ต]: Balance ${balance:.2f}
            [คำสั่งบอส]: {current_user_instruction}
            
            [ข้อมูลตลาดปัจจุบัน]:
            - ราคาปัจจุบัน: {price_data['bid']}
            - M1 (Entry Timing): RSI {m1_indicators['rsi']}, Trend {m1_indicators['trend']}
            - M15 (Price Structure): Trend {m15_indicators['trend']}, High {m15_indicators['high']}, Low {m15_indicators['low']}
            - H1 (Master Trend): Trend {h1_indicators['trend']} (EMA50)

            [ประวัติล่าสุด]: {history_context if history_context else "ไม่มีข้อมูล"}

            ภารกิจสภา:
            1. ตัดสินใจว่าจะ Buy, Sell หรือ Wait (พิจารณาความสอดคล้องของ M1 และ M15)
            2. กำหนด Lot (0.01 - 0.05) ตามความมั่นใจของสัญญาณ
            3. กำหนดระยะ TP และ SL เป็น 'จุด (Points)':
               - SL: ควรวางไว้หลัง High/Low ของ M15 หรือตามความผันผวน (แนะนำ 200-500 จุด)
               - TP: ควรมีระยะมากกว่า SL (RR > 1:1.5)

            ตอบเป็น JSON เท่านั้น:
            {{
                "decision": "buy" | "sell" | "wait",
                "strategy": "Sniper_Scalping" | "M15_Trend_Follow",
                "lot": 0.01,
                "tp_distance": 500,
                "sl_distance": 300,
                "debate_summary": "สรุปการถกเถียงระหว่าง M1, M15 และ H1",
                "reason": "เหตุผลสุดท้ายที่ประธานตัดสินใจ"
            }}
            """
            
            response = ollama.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
            data = self._safe_json_decode(response['message']['content'])
            
            if not data:
                return {"decision": "wait", "lot": 0.01, "tp_distance": 500, "sl_distance": 500}, "JSON Error"
            
            final_reason = f"[{data.get('strategy')}] M1:{m1_indicators['trend']} M15:{m15_indicators['trend']} | {data.get('debate_summary')}"
            
            return data, final_reason
        
        except Exception as e:
            print(f"❌ analyze_market Error: {e}")
            return {"decision": "wait", "lot": 0.01, "tp_distance": 500, "sl_distance": 500}, str(e)

    def check_to_close(self, current_trade_info):
        """ประชุมสภาเพื่อพิจารณาปิดไม้ โดยเน้นความอดทนมากขึ้น"""
        try:
            price_data = get_gold_price()
            # สำหรับจังหวะปิด ใช้ M5 หรือ M15 เพื่อความนิ่ง
            m5_indicators = get_indicators(timeframe=mt5.TIMEFRAME_M5)
            
            trade_type = current_trade_info['type']
            profit = current_trade_info['profit']

            prompt = f"""
            [ประชุมด่วน: พิจารณาถือครองออเดอร์]
            ออเดอร์: {trade_type} XAUUSD 
            กำไร/ขาดทุนปัจจุบัน: ${profit}
            ตลาด (M5): ราคา {price_data['bid']}, RSI {m5_indicators['rsi']}, Trend {m5_indicators['trend']}

            ภารกิจสภา:
            1. ห้ามสั่งปิด (close) เพียงเพราะติดลบเล็กน้อย เว้นแต่เทรนด์จะเปลี่ยนทิศทางชัดเจน
            2. Scalper: ถ้ากำไรถึงเป้าสั้นๆ ให้เชียร์ปิด
            3. Risk Manager: ถ้าขาดทุนใกล้จุด SL หรือกราฟเสียทรงจริงค่อยสั่งปิด
            4. หากสถานการณ์ยังปกติ ให้เลือก "hold" เพื่อรันกำไร

            ตอบเป็น JSON เท่านั้น:
            {{
                "action": "close" | "hold",
                "reason": "อธิบายสั้นๆ ว่าทำไมถึงปิดหรือถือต่อ"
            }}
            """
            response = ollama.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
            data = self._safe_json_decode(response['message']['content'])
            
            if data and data.get('action') == 'close':
                return True, data.get('reason')
            
            return False, "Hold"
        except:
            return False, "Error"

# Global Instance
gold_agent = TradingAgent()