import './globals.css';
import React from 'react';

export const metadata = {
  title: 'MindLens - Human-First Clinical Intelligence',
  description: 'Research-driven adolescent wellbeing signal synthesis across multi-rater perspectives.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,300;400;500;600&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased min-h-screen flex flex-col font-sans bg-base text-textPrimary">
        {children}
      </body>
    </html>
  );
}
