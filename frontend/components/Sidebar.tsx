"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, MessageSquare, Settings, BrainCircuit, History } from 'lucide-react';

const menuItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'AI Council', href: '/council', icon: Users },
  { name: 'Direct Chat', href: '/chat', icon: MessageSquare },
  { name: 'Trade History', href: '/history', icon: History },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#080a0f] flex flex-col p-6 h-screen shrink-0">
      <div className="flex items-center gap-3 mb-10 px-2">
        <BrainCircuit className="text-blue-500 w-8 h-8" />
        <h1 className="text-lg font-bold text-white tracking-tighter uppercase">AI COUNCIL v2</h1>
      </div>

      <nav className="space-y-2 flex-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href}>
              <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer mb-2 ${
                isActive ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20' : 'text-slate-500 hover:text-slate-200'
              }`}>
                <Icon size={20} />
                <span className="text-sm font-medium">{item.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>
      
      <div className="pt-6 border-t border-slate-800">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-500 hover:text-slate-200 rounded-xl transition-all">
          <Settings size={20} /> <span className="text-sm font-medium">Settings</span>
        </button>
      </div>
    </aside>
  );
}