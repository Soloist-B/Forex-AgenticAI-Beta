import ollama
import json
from services.mt5_service import get_gold_price, get_indicators

class AICouncil:
    def __init__(self, model_name='llama3'):
        self.model_name = model_name
        # นิสัยของแต่ละ Agent
        self.agents = {
            "Scalper": "เน้นเก็บกำไรระยะสั้น ดู RSI เป็นหลัก ชอบความไว",
            "Trend_Follower": "เน้นดู EMA 50 และโครงสร้างราคา ไม่เข้าเทรดถ้าเทรนด์ไม่ชัด",
            "Risk_Manager": "เน้นความปลอดภัย คอยค้านถ้าสัญญาณไม่ชัวร์ หรือ Lot ใหญ่เกินไป"
        }

    def get_consensus(self, user_instruction, price_data, indicators, history_context):
        print("🏛️ [Council] กำลังเริ่มการประชุมสภา AI...")
        
        # สร้าง Debate Prompt
        debate_prompt = f"""
        คุณคือ 'ประธานสภา AI' ที่ต้องสรุปความเห็นจาก Expert 3 ตัว:
        1. Scalper: {self.agents['Scalper']}
        2. Trend Follower: {self.agents['Trend_Follower']}
        3. Risk Manager: {self.agents['Risk_Manager']}

        [คำสั่งจากบอส]: {user_instruction}
        [ข้อมูลตลาด]: Price: {price_data['bid']}, RSI: {indicators['rsi']}, Trend: {indicators['trend']}
        [ประวัติ]: {history_context}

        จงจำลองการถกเถียงกันสั้นๆ ของทั้ง 3 ตัว และให้ 'มติเอกฉันท์' ออกมา
        ตอบเป็น JSON เท่านั้น:
        {{
            "consensus_decision": "buy" | "sell" | "wait",
            "final_strategy": "Scalping" | "Swing" | "Trend",
            "final_lot": 0.01,
            "debate_summary": "สรุปการเถียงกันของเหล่า Agent",
            "reason": "เหตุผลสุดท้ายที่เลือก"
        }}
        """

        try:
            response = ollama.chat(model=self.model_name, messages=[{'role': 'user', 'content': debate_prompt}])
            content = response['message']['content']
            
            start = content.find('{')
            end = content.rfind('}') + 1
            return json.loads(content[start:end])
        except Exception as e:
            print(f"❌ Council Error: {e}")
            return None

# สร้าง Instance รอไว้เลย
council_room = AICouncil()