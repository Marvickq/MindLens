'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { label: 'Overview', href: '/dashboard' },
  { label: 'Cases', href: '/cases' },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#FAF7F0' }}>
      {/* Top navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 h-14 border-b" style={{ background: '#FAF7F0', borderColor: '#E7E3DA' }}>
        <div className="flex items-center gap-10">
          <Link href="/dashboard" className="text-base font-bold tracking-tight" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
            MindLens
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                  style={{
                    color: active ? '#1C3A56' : '#5B6470',
                    background: active ? '#DCE9F2' : 'transparent',
                  }}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs" style={{ color: '#5B6470' }}>Counselor Portal</span>
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" style={{ background: '#DCE9F2', color: '#1C3A56' }}>C</div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-grow pt-14">
        {children}
      </main>
    </div>
  );
}
