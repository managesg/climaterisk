import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SeaBridge AI Sustainability Toolkit",
  description: "Physical climate risk, transition risk, nature risk, and ISSB/TCFD disclosure",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0f1117] text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
