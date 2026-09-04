'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// /cases redirects to /dashboard since the case table lives there
export default function CasesRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace('/dashboard'); }, []);
  return null;
}
