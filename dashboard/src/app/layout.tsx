import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ThreatIQ Arena',
  description: 'Autonomous Adversarial Simulation Platform — Enterprise AI Red Team / Blue Team Payment Fraud Simulation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="min-h-screen bg-[var(--canvas-cream)] text-[var(--ink-black)] antialiased">
        {children}
      </body>
    </html>
  );
}