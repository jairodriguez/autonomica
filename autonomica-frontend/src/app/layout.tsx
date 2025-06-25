import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from '@clerk/nextjs';
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
  title: "Autonomica - AI Agent Management",
  description: "Manage your AI agents and projects with Autonomica",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: undefined,
        variables: {
          colorPrimary: '#9333ea', // purple-600
          colorText: '#f3f4f6', // gray-100
          colorTextSecondary: '#9ca3af', // gray-400
          colorBackground: '#1f2937', // gray-800
          colorInputBackground: '#374151', // gray-700
          colorInputText: '#f3f4f6', // gray-100
        },
      }}
      afterSignInUrl="/projects"
      afterSignUpUrl="/projects"
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
    >
      <html lang="en">
        <body
          className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        >
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
