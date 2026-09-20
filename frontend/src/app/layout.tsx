import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
  title: "MAADT | Mission-Aware Aero-Engine Digital Twin",
  description: "Aero-Propulsion Engineering Workstation & Real-Time Digital Twin for UAV Fleet Operations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="h-full w-full bg-[#07111D] text-[#F4F7FA] antialiased overflow-hidden">
        {children}
      </body>
    </html>
  );
}
