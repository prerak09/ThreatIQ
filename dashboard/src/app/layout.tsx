import type { Metadata } from 'next';
import { Sofia_Sans } from 'next/font/google';
import './globals.css';

const sofiaSans = Sofia_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-sofia-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'ThreatIQ — Autonomous Adversarial AI Platform',
  description:
    'Autonomous Adversarial Simulation Platform — Enterprise AI Red Team / Blue Team Payment Fraud Simulation inspired by Mastercard Design System',
  icons: {
    icon: '/threatiq-logo.png',
    apple: '/threatiq-logo.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sofiaSans.variable} scroll-smooth`}>
      <body className="min-h-screen bg-[var(--canvas-cream)] text-[var(--ink-black)] antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
