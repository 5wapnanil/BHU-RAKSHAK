import type { Metadata } from "next";
import { Space_Grotesk, DM_Sans, DM_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { NetworkProvider } from "@/contexts/NetworkContext";
import { SyncStatusBar } from "@/components/SyncStatusBar";

const spaceGrotesk = Space_Grotesk({ variable: "--font-display", subsets: ["latin"], weight: ["500", "600", "700"] });
const dmSans = DM_Sans({ variable: "--font-body", subsets: ["latin"], weight: ["400", "500", "700"] });
const dmMono = DM_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "PahaarPulse Field Intelligence — Landslide Reporting & Verification",
  description: "Collect field evidence of potential landslide hazards, organize observations into structured reports, and enable administrators to review evidence and coordinate follow-up.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${dmSans.variable} ${dmMono.variable}`}>
      <body>
        <NetworkProvider>
          <Navbar />
          {children}
          <SyncStatusBar />
        </NetworkProvider>
      </body>
    </html>
  );
}
