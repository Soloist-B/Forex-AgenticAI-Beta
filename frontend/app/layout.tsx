import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
// 1. นำเข้า Sidebar (เช็ค Path ให้ตรงกับที่บอสวางไฟล์ไว้นะครับ)
import Sidebar from "@/components/Sidebar"; 

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Council v2 - Trading Terminal",
  description: "Agentic AI System for XAUUSD Trading",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="h-full bg-[#05070a] text-slate-200 overflow-hidden flex">
        {/* 2. วาง Sidebar ไว้ตรงนี้ เพื่อให้มันโชว์ทุกหน้า */}
        <Sidebar />

        {/* 3. ส่วน Content ขวามือที่จะเปลี่ยนไปตาม Route */}
        <main className="flex-1 h-screen overflow-y-auto bg-[#05070a]">
          {children}
        </main>
      </body>
    </html>
  );
}