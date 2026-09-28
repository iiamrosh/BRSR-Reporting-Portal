import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";
import { DemoUserProvider } from "@/components/DemoUserContext";

export const metadata: Metadata = { title: "BRSR Nexus", description: "Governed ESG reporting for complex organizations" };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) { return <html lang="en"><body><DemoUserProvider><AppShell>{children}</AppShell></DemoUserProvider></body></html>; }
