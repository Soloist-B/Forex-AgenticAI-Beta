"use client";
import { useState, useEffect, useCallback } from 'react';
import { 
  Activity, RefreshCcw, Wallet, Terminal, 
  TrendingUp, Zap, ShieldCheck, PieChart, 
  BarChart3, ArrowUpRight, ArrowDownRight, Target
} from 'lucide-react';

interface MarketData {
  price: number;
  balance: number;
  equity: number;
  profit_total: number;
  current_trade: { type: string; price: number; profit: number } | null;
  status: string;
  indicators?: { rsi: number; ema_20: number; ema_50: number; trend: string; };
}

export default function DashboardPage() {
  const [data, setData] = useState<MarketData>({ 
    price: 0, balance: 0, equity: 0, profit_total: 0, current_trade: null, status: "Connecting..." 
  });
  const [lastUpdate, setLastUpdate] = useState("");
  
  // สมมติทุนเริ่มต้น (Initial Capital) ของบอสคือ $50 หรือ $100
  // บอสสามารถปรับตัวเลขนี้ตามจริงได้เลยครับ
  const initialCapital = 50.00; 
  const totalProfit = data.profit_total || 0;
  const roi = ((totalProfit / initialCapital) * 100).toFixed(2);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/status');
      const result = await res.json();
      setData(result);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err) {
      setData(prev => ({ ...prev, status: "Offline" }));
    }
  }, []);

  useEffect(() => {
    const initFetch = async () => {
      await fetchStatus();
    };
    initFetch();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return (
    <div className="p-8 max-w-7xl mx-auto w-full animate-in fade-in duration-700 overflow-y-auto h-screen pb-20 no-scrollbar">
      
      {/* --- HEADER --- */}
      <header className="mb-8 flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-white uppercase tracking-tighter flex items-center gap-3">
            <LayoutDashboardIcon className="text-blue-500" size={28} /> Market Intelligence
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            <span className="text-blue-400 font-mono">XAUUSD.iux</span> • Node-Llama3 Active • <span className="text-slate-400">{lastUpdate}</span>
          </p>
        </div>
        <div className={`px-4 py-2 rounded-2xl border ${data.status === 'Offline' ? 'border-red-500/30 bg-red-500/5 text-red-400' : 'border-emerald-500/30 bg-emerald-500/5 text-emerald-400'} flex items-center gap-2 shadow-lg`}>
          <div className={`w-2 h-2 rounded-full ${data.status === 'Offline' ? 'bg-red-500' : 'bg-emerald-500'} animate-pulse`}></div>
          <span className="text-[10px] font-black tracking-widest uppercase">{data.status}</span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* --- MAIN PRICE CARD --- */}
        <div className="lg:col-span-2 bg-gradient-to-br from-slate-900 via-slate-950 to-black border border-slate-800 rounded-[3rem] p-10 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-12 opacity-[0.03] group-hover:opacity-[0.07] transition-all duration-700 rotate-12">
            <TrendingUp size={280} />
          </div>
          
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-4">
              <span className="bg-yellow-500/10 text-yellow-500 p-2 rounded-xl border border-yellow-500/20">
                <Zap size={18} />
              </span>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.3em]">Spot Gold / XAUUSD</p>
            </div>
            
            <h2 className="text-9xl font-mono font-bold text-white tracking-tighter italic drop-shadow-2xl">
              {data.price?.toFixed(2) ?? "0.00"}
            </h2>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <div className="bg-blue-500/10 text-blue-400 px-4 py-2 rounded-2xl text-xs font-bold border border-blue-500/20 flex items-center gap-2">
                <RefreshCcw size={14} className="animate-spin-slow" /> LIVE SYNC
              </div>
              <div className="bg-slate-800/50 text-slate-300 px-4 py-2 rounded-2xl text-xs font-mono border border-slate-700/50">
                RSI: <span className={Number(data.indicators?.rsi) > 70 ? 'text-red-400' : Number(data.indicators?.rsi) < 30 ? 'text-green-400' : 'text-blue-400'}>
                  {data.indicators?.rsi ?? "--"}
                </span>
              </div>
              <div className="bg-slate-800/50 text-slate-300 px-4 py-2 rounded-2xl text-xs font-mono border border-slate-700/50 uppercase">
                Trend: <span className={data.indicators?.trend === 'UP' ? 'text-green-400' : 'text-red-400'}>
                  {data.indicators?.trend ?? "Analyzing..."}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* --- PERFORMANCE ANALYTICS CARD --- */}
        <div className="bg-[#0a0c12] border border-slate-800 rounded-[3rem] p-8 shadow-xl flex flex-col relative overflow-hidden">
          <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-blue-500/5 blur-[80px]"></div>
          
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6 text-slate-500 font-bold uppercase tracking-widest text-[10px]">
              <Wallet size={16} className="text-blue-500" /> Portfolio Growth
            </div>
            <p className="text-5xl font-mono font-bold text-white tracking-tight leading-none mb-3">
              ${data.balance?.toLocaleString()}
            </p>
            <div className="flex items-center gap-2">
              <span className={`flex items-center text-xs font-bold ${Number(roi) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {Number(roi) >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />} {roi}%
              </span>
              <span className="text-slate-600 text-[10px] uppercase font-bold tracking-tighter">ROI from ${initialCapital}</span>
            </div>
          </div>

          <div className="space-y-4 pt-6 border-t border-slate-800/50">
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-500 flex items-center gap-2"><PieChart size={14} /> Equity</span>
              <span className="text-sm font-mono font-bold text-slate-200">${data.equity?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-500 flex items-center gap-2"><BarChart3 size={14} /> Net Profit</span>
              <span className={`text-sm font-mono font-bold ${totalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {totalProfit >= 0 ? '+' : ''}${totalProfit.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center pt-4 border-t border-slate-800/30">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-tighter">Security Mode</span>
              <div className="flex items-center gap-1 text-blue-400 text-[10px] font-black bg-blue-500/10 px-2 py-1 rounded-lg border border-blue-500/20">
                <ShieldCheck size={12} /> AI-PROTECTED
              </div>
            </div>
          </div>
        </div>

        {/* --- LIVE TRADE MONITOR --- */}
        <div className="lg:col-span-3 bg-[#080a0f] border border-slate-800 rounded-[2.5rem] p-8 shadow-inner">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-3 text-slate-400 font-bold uppercase tracking-widest text-[10px]">
              <Target size={16} className="text-red-500" /> Active Execution Layer
            </div>
            <div className="text-[9px] font-mono text-slate-600 uppercase">Latency: 12ms | MT5: Bridge-Connected</div>
          </div>

          {data.current_trade ? (
            <div className="bg-gradient-to-r from-blue-600/10 to-transparent rounded-[2rem] p-8 flex flex-col md:flex-row justify-between items-center border border-blue-500/10 relative overflow-hidden group">
              <div className="absolute left-0 top-0 h-full w-1 bg-blue-500"></div>
              
              <div className="flex items-center gap-8 mb-4 md:mb-0">
                <div className={`p-6 rounded-[1.5rem] shadow-2xl ${data.current_trade.type === 'BUY' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                  <Zap size={32} className="animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className={`text-2xl font-black italic tracking-tighter ${data.current_trade.type === 'BUY' ? 'text-emerald-500' : 'text-red-400'}`}>
                      {data.current_trade.type} ORDER
                    </p>
                    <span className="bg-slate-800 text-slate-400 text-[9px] px-2 py-0.5 rounded-full font-bold uppercase">XAUUSD</span>
                  </div>
                  <p className="text-slate-500 font-mono text-sm">Entry Price: <span className="text-white">${data.current_trade.price?.toFixed(2)}</span></p>
                </div>
              </div>

              <div className="text-center md:text-right">
                <p className={`text-5xl font-mono font-bold leading-none mb-2 ${data.current_trade.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {data.current_trade.profit >= 0 ? '+' : ''}{data.current_trade.profit?.toFixed(2)}
                </p>
                <div className="flex items-center justify-center md:justify-end gap-2">
                   <div className={`w-2 h-2 rounded-full ${data.current_trade.profit >= 0 ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'}`}></div>
                   <p className="text-slate-600 text-[10px] font-black uppercase tracking-widest">Floating Real-time P/L</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 border-2 border-dashed border-slate-800/50 rounded-[2rem] bg-slate-900/5 transition-colors hover:bg-slate-900/10">
              <div className="relative mb-4">
                <Activity size={48} className="text-slate-800 animate-pulse" />
                <div className="absolute inset-0 bg-blue-500/10 blur-xl rounded-full"></div>
              </div>
              <p className="text-sm text-slate-500 font-bold uppercase tracking-widest mb-1">Council is Scanning Market</p>
              <p className="text-[10px] text-slate-700 font-mono">Waiting for high-probability setup... (EMA 20/50 Confirming)</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- 1. นิยาม Interface ให้รองรับ size อย่างถูกต้อง ---
interface CustomIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

// --- 2. แก้ฟังก์ชันให้แกะ size ออกมาใช้ (Destructuring) ---
function LayoutDashboardIcon({ size = 24, ...props }: CustomIconProps) {
  return (
    <svg 
      {...props} 
      width={size}   // นำค่า size มาใส่ที่นี่
      height={size}  // นำค่า size มาใส่ที่นี่
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    >
      <rect width="7" height="9" x="3" y="3" rx="1" />
      <rect width="7" height="5" x="14" y="3" rx="1" />
      <rect width="7" height="9" x="14" y="12" rx="1" />
      <rect width="7" height="5" x="3" y="16" rx="1" />
    </svg>
  );
}