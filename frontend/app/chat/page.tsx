"use client";
import { useState, useEffect, useRef } from 'react';
import { 
  Send, Zap, User, Bot, Terminal, 
  Cpu, ShieldCheck, Loader2 
} from 'lucide-react';

interface Message {
  role: 'user' | 'bot';
  content: string;
  status?: 'sending' | 'success' | 'error';
}

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', content: 'สวัสดีครับบอส ผมประธานสภา AI เตรียมพร้อมรับคำสั่งพิเศษสำหรับ XAUUSD แล้วครับ ไม้ถัดไปอยากเน้นกลยุทธ์ไหนสั่งมาได้เลย!' }
  ]);
  
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto Scroll เมื่อมีข้อความใหม่
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    
    const userMsg: Message = { role: 'user', content: input, status: 'sending' };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'custom_command', prompt: currentInput })
      });
      
      const data = await res.json();
      
      // จำลอง AI คิดนิดนึงให้ดูสมจริง
      setTimeout(() => {
        setMessages(prev => [
          ...prev.map((m, idx) => idx === prev.length - 1 ? { ...m, status: 'success' } as Message : m),
          { role: 'bot', content: `รับทราบครับบอส! สภา AI รับมติใหม่: "${data.message}" ผมจะเริ่มใช้กลยุทธ์นี้ใน Cycle หน้าทันทีครับ` }
        ]);
        setIsTyping(false);
      }, 800);

    } catch (e) {
      setMessages(prev => [
        ...prev.map((m, idx) => idx === prev.length - 1 ? { ...m, status: 'error' } as Message : m),
        { role: 'bot', content: '⚠️ ติดต่อสภา AI ไม่ได้ครับบอส ดูเหมือน Backend จะ Offline' }
      ]);
      setIsTyping(false);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col max-w-5xl mx-auto animate-in fade-in duration-700">
      
      {/* --- HEADER --- */}
      <header className="mb-6 flex justify-between items-center px-4">
        <div>
          <h2 className="text-3xl font-black text-white flex items-center gap-3 tracking-tighter uppercase">
            <Cpu className="text-blue-500" size={32} /> Command Center
          </h2>
          <p className="text-[10px] text-slate-500 font-mono mt-1 uppercase tracking-widest">
            Direct Interface • LLM-Pipeline: <span className="text-blue-400">Stable</span>
          </p>
        </div>
        <div className="flex items-center gap-4 bg-slate-900/50 p-2 px-4 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-[10px] font-bold text-slate-400 uppercase font-mono">Council Online</span>
          </div>
          <ShieldCheck size={18} className="text-blue-500" />
        </div>
      </header>

      {/* --- CHAT CONTAINER --- */}
      <div className="flex-1 bg-gradient-to-b from-slate-900/50 to-black/50 border border-slate-800 rounded-[3rem] flex flex-col overflow-hidden shadow-2xl backdrop-blur-sm relative">
        <div className="absolute inset-0 opacity-[0.02] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
        
        {/* Messages Area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-10 space-y-8 no-scrollbar">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
              <div className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                
                {/* Avatar */}
                <div className={`p-3 rounded-2xl h-fit shadow-xl ${
                  msg.role === 'user' 
                  ? 'bg-blue-600 text-white shadow-blue-600/20' 
                  : 'bg-slate-800 text-blue-400 border border-slate-700 shadow-black'
                }`}>
                  {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                </div>

                {/* Bubble */}
                <div className="space-y-2">
                  <div className={`p-5 rounded-[2rem] text-sm leading-relaxed shadow-lg ${
                    msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none' 
                    : 'bg-[#151921] text-slate-200 border border-slate-800 rounded-tl-none'
                  }`}>
                    {msg.content}
                  </div>
                  
                  {/* Status Indicator for User messages */}
                  {msg.role === 'user' && msg.status && (
                    <p className={`text-[9px] font-mono text-right uppercase tracking-tighter ${
                      msg.status === 'success' ? 'text-emerald-500' : msg.status === 'error' ? 'text-red-500' : 'text-slate-500'
                    }`}>
                      {msg.status === 'sending' ? 'Transmitting to Council...' : msg.status === 'success' ? 'Council Received' : 'Transmission Failed'}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start animate-in fade-in">
              <div className="flex gap-4 items-center bg-slate-800/30 p-4 px-6 rounded-full border border-slate-800">
                <Loader2 size={16} className="text-blue-500 animate-spin" />
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest font-bold">AI Council is debating...</span>
              </div>
            </div>
          )}
        </div>

        {/* --- INPUT AREA --- */}
        <div className="p-8 bg-black/40 border-t border-slate-800/50 backdrop-blur-xl">
          <div className="flex gap-4 bg-slate-900/80 p-2 pl-6 rounded-[2rem] border border-slate-700 focus-within:border-blue-500 transition-all shadow-inner group">
            <div className="flex items-center text-slate-600 group-focus-within:text-blue-500 transition-colors">
              <Terminal size={18} />
            </div>
            <input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Enter specific trading instructions..."
              className="flex-1 bg-transparent border-none py-4 text-sm text-white placeholder:text-slate-600 outline-none font-mono"
            />
            <button 
              onClick={handleSend} 
              disabled={isTyping}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white p-4 px-6 rounded-[1.5rem] transition-all flex items-center gap-2 group shadow-lg shadow-blue-600/20 active:scale-95"
            >
              <span className="text-xs font-black uppercase tracking-widest hidden md:block">Transmit</span>
              <Send size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </button>
          </div>
          <p className="mt-4 text-center text-[9px] text-slate-700 font-mono uppercase tracking-[0.2em]">
            Warning: Direct commands override council technical analysis for the next execution cycle.
          </p>
        </div>
      </div>
    </div>
  );
}