"use client";
import { useState, useEffect } from 'react';
import { 
  BrainCircuit, Activity, Zap, Server, 
  MessageSquareQuote, Terminal, Cpu, ShieldCheck,
  RefreshCcw // เพิ่มตัวนี้
} from 'lucide-react';

// --- 1. กำหนด Type ให้ชัดเจน ---
interface DebateLog {
  id: number;
  timestamp: string;
  decision: string;
  strategy: string;
  price: number;
  reason: string;
}

const colorMap: Record<string, { bg: string, text: string, border: string }> = {
  blue: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" },
  emerald: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/20" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/20" },
};

export default function CouncilPage() {
  const [activeAgents] = useState([
    { id: 1, name: "Gold Scalper", task: "RSI & EMA Breakdown", status: "Active", type: "Aggressive", color: "blue" },
    { id: 2, name: "Trend Follower", task: "Price Action Structure", status: "Monitoring", type: "Conservative", color: "emerald" },
    { id: 3, name: "Risk Manager", task: "Drawdown Control", status: "Secured", type: "Safety", color: "purple" },
  ]);

  const [recentDebates, setRecentDebates] = useState<DebateLog[]>([]);

  // --- 2. Logic การดึงข้อมูลการถกเถียง ---
  useEffect(() => {
    const fetchDebates = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/history');
        if (!res.ok) return;
        const result = await res.json();
        // เอามาแค่ 3 อันล่าสุด เพื่อให้หน้าจอไม่ยาวเกินไป
        setRecentDebates(result.slice(0, 3));
      } catch (err) {
        console.error("Debate fetch error:", err);
      }
    };
    
    fetchDebates();
    const interval = setInterval(fetchDebates, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto w-full animate-in fade-in duration-700 overflow-y-auto h-full no-scrollbar pb-20">
      
      {/* --- HEADER --- */}
      <header className="mb-10 flex justify-between items-end px-4">
        <div className="space-y-1">
          <h2 className="text-3xl font-black text-white uppercase tracking-tighter flex items-center gap-3">
            <Cpu className="text-blue-500" /> AI Council Chamber
          </h2>
          <p className="text-slate-500 text-xs font-mono uppercase tracking-[0.2em]">
            Strategic Decision Logic • <span className="text-blue-400 italic">Node: Llama3-8B</span>
          </p>
        </div>
        <div className="hidden md:flex items-center gap-4 bg-slate-900/40 p-3 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_#22c55e]"></div>
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Multi-Agent Sync</span>
          </div>
          <ShieldCheck size={18} className="text-blue-500 opacity-50" />
        </div>
      </header>

      {/* --- AGENT CARDS GRID --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {activeAgents.map((agent) => {
          const colors = colorMap[agent.color] || colorMap.blue;
          return (
            <div key={agent.id} className="bg-[#0a0c12] border border-slate-800/80 p-8 rounded-[3rem] hover:border-blue-500/30 transition-all group relative overflow-hidden shadow-2xl">
              <div className={`absolute -right-4 -top-4 w-24 h-24 ${colors.bg} rounded-full blur-[60px] opacity-0 group-hover:opacity-100 transition-opacity duration-700`}></div>
              
              <div className="flex justify-between items-start mb-6 relative z-10">
                <div className={`p-4 rounded-2xl ${colors.bg} ${colors.text} border ${colors.border} shadow-inner`}>
                  <BrainCircuit size={28} />
                </div>
                <span className="text-[9px] font-black bg-slate-800 text-slate-400 px-3 py-1 rounded-full border border-slate-700 uppercase tracking-widest">
                  {agent.type}
                </span>
              </div>
              
              <h3 className="text-xl font-black text-white mb-2 group-hover:text-blue-400 transition-colors uppercase tracking-tight relative z-10">
                {agent.name}
              </h3>
              <p className="text-sm text-slate-500 mb-6 leading-relaxed font-medium relative z-10">
                {agent.task}
              </p>
              
              <div className="pt-6 border-t border-slate-800/50 flex items-center justify-between relative z-10">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${agent.status === 'Active' || agent.status === 'Secured' ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-blue-500 shadow-[0_0_8px_#3b82f6]'} animate-pulse`}></div>
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">
                    {agent.status}
                  </span>
                </div>
                <Activity size={14} className="text-slate-700 group-hover:text-blue-500 transition-colors" />
              </div>
            </div>
          );
        })}
      </div>

      {/* --- LIVE DEBATE FEED --- */}
      <div className="bg-[#07090e] border border-slate-800 rounded-[3rem] p-10 shadow-2xl relative">
        <div className="flex items-center justify-between mb-10 border-b border-slate-800/60 pb-8">
          <div className="flex items-center gap-4">
            <div className="bg-yellow-500/10 p-4 rounded-2xl border border-yellow-500/20 text-yellow-500 shadow-[0_0_20px_rgba(234,179,8,0.1)]">
              <MessageSquareQuote size={24} />
            </div>
            <div>
              <h3 className="text-xl font-black text-white uppercase tracking-tight">Council Transcript</h3>
              <p className="text-xs text-slate-500 font-medium italic mt-1">การจำลองการถกเถียงและสรุปมติโดยประธานสภา AI</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500 bg-black/40 px-4 py-2 rounded-xl border border-slate-800">
            <Terminal size={14} className="text-blue-500" /> SESSION_LOGS: ACTIVE
          </div>
        </div>

        <div className="space-y-10 relative before:absolute before:left-[11px] before:top-4 before:bottom-4 before:w-[1px] before:bg-gradient-to-b before:from-blue-500/50 before:via-slate-800 before:to-transparent">
          {recentDebates.length > 0 ? recentDebates.map((debate) => (
            <div key={debate.id} className="group relative pl-12 transition-all">
              {/* Timeline Dot */}
              <div className="absolute left-0 top-1.5 w-[23px] h-[23px] rounded-full bg-[#07090e] border border-slate-800 group-hover:border-blue-500 transition-colors z-10 flex items-center justify-center">
                 <div className="w-1.5 h-1.5 rounded-full bg-slate-700 group-hover:bg-blue-500 animate-pulse shadow-[0_0_5px_currentColor]"></div>
              </div>
              
              <div className="flex flex-col gap-4 bg-[#0d1117]/40 p-6 rounded-[2rem] border border-transparent group-hover:border-slate-800 group-hover:bg-[#0d1117]/60 transition-all shadow-sm">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-4">
                    <span className={`text-[10px] font-black px-3 py-1 rounded-lg uppercase border tracking-widest ${
                      debate.decision === 'buy' ? 'text-green-400 border-green-500/20 bg-green-500/5 shadow-[0_0_10px_rgba(34,197,94,0.1)]' : 
                      debate.decision === 'sell' ? 'text-red-400 border-red-500/20 bg-red-500/5 shadow-[0_0_10px_rgba(239,68,68,0.1)]' : 
                      'text-slate-400 border-slate-500/20 bg-slate-500/5'
                    }`}>
                      {debate.decision}
                    </span>
                    <span className="text-[10px] font-mono font-bold text-slate-500 tracking-wider">{debate.timestamp}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-black text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded uppercase tracking-widest">{debate.strategy}</span>
                  </div>
                </div>

                {/* ส่วนการถกเถียง Reason */}
                <div className="relative">
                  <div className="absolute -left-2 top-0 text-slate-800 text-4xl font-serif">&quot;</div>
                  <p className="text-sm text-slate-200 leading-relaxed font-medium italic pl-4 border-l border-slate-800/50">
                    {debate.reason}
                  </p>
                </div>

                <div className="flex justify-end border-t border-slate-800/40 pt-4 mt-2">
                   <div className="flex items-center gap-2">
                      <span className="text-[9px] font-black text-slate-600 uppercase tracking-[0.2em]">Executed At</span>
                      <span className="text-[10px] font-mono font-bold text-white bg-slate-900 px-3 py-1 rounded-lg border border-slate-800 shadow-inner">
                        ${debate.price.toLocaleString()}
                      </span>
                   </div>
                </div>
              </div>
            </div>
          )) : (
            <div className="text-center py-20">
              <div className="inline-block animate-spin-slow mb-4 opacity-20">
                <RefreshCcw size={40} className="text-blue-500" />
              </div>
              <p className="text-xs text-slate-600 font-black uppercase tracking-[0.4em]">Waiting for Council Consensus...</p>
            </div>
          )}
        </div>
      </div>

      {/* FOOTER TIP */}
      <div className="mt-10 flex items-center gap-4 px-8 py-6 bg-blue-600/5 border border-blue-500/10 rounded-[2rem]">
        <Zap className="text-yellow-500 shrink-0" size={20} />
        <p className="text-[10px] text-slate-400 uppercase tracking-widest leading-relaxed font-bold">
          <span className="text-blue-400">Security Info:</span> การตัดสินใจในสภานี้ถูกควบคุมโดย <span className="text-white underline decoration-blue-500/50">Risk Management Layer</span> เพื่อป้องกัน Overtrade ในกรณีที่ตลาดผันผวนสูง
        </p>
      </div>
    </div>
  );
}

function RefreshCcwIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg 
      {...props} 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" 
      height="24" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    >
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 16h5v5" />
    </svg>
  );
}