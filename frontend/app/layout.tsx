import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SeaBridge AI Sustainability Toolkit",
  description: "Physical climate risk · Transition risk · Nature risk · ISSB IFRS S2 / TCFD / TNFD",
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
      <body className="min-h-full flex flex-col bg-gray-50">
        <nav className="bg-slate-900 text-white px-6 py-3 flex items-center gap-6 text-sm">
          <Link href="/" className="font-bold text-white text-base tracking-tight">
            SeaBridge
          </Link>
          <Link href="/properties" className="text-slate-300 hover:text-white transition-colors">
            Properties
          </Link>
          <Link href="/agent" className="text-slate-300 hover:text-white transition-colors">
            AI Agent
          </Link>
          <Link href="/assessment" className="text-slate-300 hover:text-white transition-colors">
            Scorecards
          </Link>
          <Link href="/disclosure" className="text-slate-300 hover:text-white transition-colors">
            Disclosure
          </Link>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
