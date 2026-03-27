"use client";
import { useState, useEffect, useCallback } from 'react';
import { 
  History, RefreshCcw, ArrowUpRight, ArrowDownRight, 
  TrendingUp, Wallet, Calendar, Search, 
  CheckCircle2, XCircle, BarChart2
} from 'lucide-react';

interface TradeLog {
  id: number;
  timestamp: string;
  decision: string;
  strategy: string;
  lot: number;
  price: number;
  reason: string;
  profit: number; // ผลกำไร/ขาดทุนที่เกิดขึ้นจริง
  status?: string; // เช่น 'Closed' หรือ 'Open'
}

export default function TradeHistoryPage() {
  const [historyData, setHistoryData] = useState<TradeLog[]>([]);
  const [loading, setLoading] = useState(true);

  // สถิติเบื้องต้น
  const totalProfit = historyData.reduce((sum, trade) => sum + (trade.profit || 0), 0);
  const winCount = historyData.filter(trade => (trade.profit || 0) > 0).length;
  const winRate = historyData.length > 0 ? ((winCount / historyData.length) * 100).toFixed(1) : "0";

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('http://127.0.0.1:8000/api/history');
      const result = await res.json();
      // เรียงลำดับเอาอันใหม่ล่าสุดขึ้นก่อน
      setHistoryData(result.reverse());
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000); // อัปเดตทุก 10 วินาที
    return () => clearInterval(interval);
  }, [fetchHistory]);

  return (
    <div className="p-8 max-w-7xl mx-auto w-full animate-in fade-in duration-700 h-full overflow-y-auto no-scrollbar pb-20">
      
      {/* --- HEADER & SUMMARY STATS --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
        <div>
          <h2 className="text-3xl font-black text-white uppercase tracking-tighter flex items-center gap-3">
            <BarChart2 className="text-blue-500" size={32} /> Performance Ledger
          </h2>
          <p className="text-slate-500 text-xs font-mono mt-1 uppercase tracking-[0.2em]">Verified Exchange Execution History</p>
        </div>

        <div className="flex gap-4">
          <div className="bg-slate-900/50 border border-slate-800 p-4 px-6 rounded-[1.5rem] flex flex-col">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Total P/L</span>
            <span className={`text-xl font-mono font-black ${totalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {totalProfit >= 0 ? '+' : ''}${totalProfit.toFixed(2)}
            </span>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 p-4 px-6 rounded-[1.5rem] flex flex-col">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Win Rate</span>
            <span className="text-xl font-mono font-black text-blue-400">{winRate}%</span>
          </div>
          <button 
            onClick={fetchHistory}
            className="bg-blue-600 hover:bg-blue-500 text-white p-4 rounded-2xl transition-all self-center shadow-lg shadow-blue-600/20"
          >
            <RefreshCcw size={20} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* --- TRADE TABLE --- */}
      <div className="bg-[#080a0f] border border-slate-800 rounded-[2.5rem] overflow-hidden shadow-2xl relative">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/[0.02] to-transparent pointer-events-none"></div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-black/40 text-slate-500 text-[10px] uppercase tracking-[0.2em] font-black border-b border-slate-800">
              <tr>
                <th className="p-6">Time / ID</th>
                <th className="p-6">Type</th>
                <th className="p-6">Strategy</th>
                <th className="p-6">Volume</th>
                <th className="p-6">Execution Price</th>
                <th className="p-6 text-right">Net Profit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/30">
              {historyData.length > 0 ? historyData.map((log) => (
                <tr key={log.id} className="hover:bg-blue-600/[0.03] transition-colors group">
                  <td className="p-6">
                    <div className="flex flex-col">
                      <span className="text-[11px] font-mono text-slate-300 group-hover:text-blue-400 transition-colors font-bold">{log.timestamp}</span>
                      <span className="text-[9px] text-slate-600 font-mono italic">#ID-{log.id.toString().padStart(5, '0')}</span>
                    </div>
                  </td>
                  <td className="p-6">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${log.decision === 'buy' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'}`}></div>
                      <span className={`text-[11px] font-black uppercase tracking-widest ${log.decision === 'buy' ? 'text-emerald-500' : 'text-red-400'}`}>
                        {log.decision}
                      </span>
                    </div>
                  </td>
                  <td className="p-6">
                    <span className="text-[10px] font-bold text-slate-400 bg-slate-800/40 px-3 py-1 rounded-lg border border-slate-700/50 uppercase tracking-tighter">
                      {log.strategy}
                    </span>
                  </td>
                  <td className="p-6">
                    <span className="text-xs font-mono font-black text-slate-200">{log.lot.toFixed(2)} <span className="text-[9px] text-slate-600 font-bold">LOTS</span></span>
                  </td>
                  <td className="p-6">
                    <span className="text-xs font-mono text-white font-bold">${log.price.toLocaleString()}</span>
                  </td>
                  <td className="p-6 text-right">
                    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl font-mono font-black text-sm ${
                      (log.profit || 0) >= 0 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'
                    }`}>
                      {(log.profit || 0) >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      ${(log.profit || 0).toFixed(2)}
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} className="p-32 text-center">
                    <div className="flex flex-col items-center opacity-20">
                      <History size={48} className="text-slate-500 mb-4" />
                      <p className="text-xs font-mono uppercase tracking-[0.3em] text-slate-400">Zero Execution Data Found</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- FOOTER LOGS --- */}
      <footer className="mt-8 flex justify-between items-center px-6 text-slate-600">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
          <CheckCircle2 size={14} className="text-emerald-500" /> All trades verified by MT5-Server
        </div>
        <div className="text-[10px] font-mono italic">
          Total Executions: {historyData.length} trades
        </div>
      </footer>
    </div>
  );
}