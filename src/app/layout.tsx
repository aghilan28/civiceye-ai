import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { PwaProvider } from "@/components/providers/pwa-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"),
  title: {
    default: "CivicEye | AI Civic Infrastructure Intelligence",
    template: "%s | CivicEye"
  },
  description:
    "AI-powered civic infrastructure monitoring for potholes, drainage overflow, streetlight failures, water leakage, garbage accumulation, and road damage.",
  keywords: [
    "civic technology",
    "smart city",
    "computer vision",
    "infrastructure monitoring",
    "pothole detection",
    "AI dashboard"
  ],
  authors: [{ name: "CivicEye" }],
  openGraph: {
    title: "CivicEye",
    description: "AI civic infrastructure intelligence for faster, safer, cleaner cities.",
    type: "website",
    siteName: "CivicEye"
  },
  twitter: {
    card: "summary_large_image",
    title: "CivicEye",
    description: "AI civic infrastructure intelligence for faster, safer, cleaner cities."
  },
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    title: "CivicEye",
    statusBarStyle: "black-translucent"
  }
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
  themeColor: "#050816"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <ThemeProvider attribute="class" defaultTheme="dark" forcedTheme="dark" enableSystem={false}>
          <PwaProvider />
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
