import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RADAR-X",
  description: "Market Intelligence OS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased h-screen overflow-hidden text-zinc-200">
        {children}
      </body>
    </html>
  );
}
