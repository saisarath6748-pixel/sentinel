import type { Metadata } from "next";
import { Roboto_Mono } from "next/font/google";
import "./globals.css";
import { AuthLayoutWrapper } from "@/components/AuthLayoutWrapper";

const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Abuse-Ring Sentinel",
  description: "Real-time Fraud Ring Detection — Razorpay Buildathon",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${robotoMono.variable} ${robotoMono.className} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthLayoutWrapper>{children}</AuthLayoutWrapper>
      </body>
    </html>
  );
}
