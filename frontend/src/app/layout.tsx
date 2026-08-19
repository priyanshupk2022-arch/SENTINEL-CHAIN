import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SENTINEL-CHAIN // Autonomous Cyber Threat Intelligence Self-Healing Engine",
  description: "Autonomous self-healing proxy pipeline for Bright Data Scraper Studio & Gemini 3.1 Pro",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased h-screen overflow-hidden bg-[#070A10] text-slate-100 selection:bg-sky-500/30 selection:text-sky-300">
        {children}
      </body>
    </html>
  );
}
