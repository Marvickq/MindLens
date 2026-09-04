'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';

interface CaseItem {
  id: string;
  display_name: string;
  external_reference?: string;
  status: string;
  created_at: string;
  raters?: { parent: boolean; teacher: boolean; adolescent: boolean };
}

interface Summary {
  awaiting_responses: number;
  ready_for_review: number;
  under_review: number;
  completed: number;
}

const MOCK_CASES: CaseItem[] = [];

function statusLabel(status: string) {
  switch (status) {
    case 'READY_FOR_REVIEW': return 'Ready for Review';
    case 'WAITING_FOR_RESPONSES': return 'Awaiting Responses';
    case 'UNDER_REVIEW': return 'Under Review';
    case 'COMPLETED': return 'Completed';
    default: return status.replace(/_/g, ' ');
  }
}

function statusStyle(status: string) {
  switch (status) {
    case 'READY_FOR_REVIEW': return { background: '#DCE9F2', color: '#1C3A56' };
    case 'WAITING_FOR_RESPONSES': return { background: '#E7E3DA', color: '#5B6470' };
    case 'UNDER_REVIEW': return { background: '#C7C0DE', color: '#1C3A56' };
    case 'COMPLETED': return { background: '#d4ede9', color: '#2a6b67' };
    default: return { background: '#E7E3DA', color: '#5B6470' };
  }
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ago`;
}

function RaterDots({ raters }: { raters: { parent: boolean; teacher: boolean; adolescent: boolean } }) {
  return (
    <div className="flex items-center gap-1.5">
      {(['parent', 'teacher', 'adolescent'] as const).map((r) => (
        <span
          key={r}
          title={raters[r] ? `${r} — responded` : `${r} — pending`}
          className="w-2.5 h-2.5 rounded-full border"
          style={{
            background: raters[r] ? '#4C9A94' : 'transparent',
            borderColor: raters[r] ? '#4C9A94' : '#5B6470',
          }}
        />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary>({
    awaiting_responses: 0,
    ready_for_review: 0,
    under_review: 0,
    completed: 0,
  });
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [newCaseName, setNewCaseName] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('MindLens_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    fetch('http://localhost:8000/api/v1/dashboard/summary', { headers })
      .then((r) => r.json()).then(setSummary).catch(() => {});
    fetch('http://localhost:8000/api/v1/cases', { headers })
      .then((r) => r.json())
      .then((d) => { if (Array.isArray(d)) setCases(d); })
      .catch(() => {});
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseName.trim()) return;
    const mock: CaseItem = {
      id: crypto.randomUUID(),
      display_name: newCaseName,
      external_reference: `MF-0${Math.floor(Math.random() * 9000) + 1000}`,
      status: 'WAITING_FOR_RESPONSES',
      created_at: new Date().toISOString(),
      raters: { parent: false, teacher: false, adolescent: false },
    };
    try {
      const token = localStorage.getItem('MindLens_token');
      const res = await fetch('http://localhost:8000/api/v1/cases', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ display_name: newCaseName }),
      });
      if (res.ok) {
        const created = await res.json();
        // API returns case_id, frontend expects id
        const normalized = { ...created, id: created.case_id || created.id };
        setCases([normalized, ...cases]);
      } else {
        setCases([mock, ...cases]);
      }
    } catch {
      setCases([mock, ...cases]);
    }
    setNewCaseName('');
    setShowModal(false);
  };

  const statCards = [
    { label: 'Awaiting Responses', value: summary.awaiting_responses },
    { label: 'Ready for Review', value: summary.ready_for_review },
    { label: 'Under Review', value: summary.under_review },
    { label: 'Completed', value: summary.completed },
  ];

  return (
    <div className="px-8 py-8 max-w-7xl mx-auto space-y-8">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
            Overview
          </h1>
          <p className="text-sm mt-0.5" style={{ color: '#5B6470' }}>
            Active caseload · Greenwood School District
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors"
          style={{ background: '#1C3A56', color: '#fff' }}
        >
          <span className="text-lg leading-none">+</span> New Case
        </button>
      </div>

      {/* Stat strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map(({ label, value }) => (
          <div
            key={label}
            className="rounded-xl p-5 border"
            style={{ background: '#fff', borderColor: '#E7E3DA' }}
          >
            <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: '#5B6470' }}>
              {label}
            </p>
            <p className="text-3xl font-semibold" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Case table */}
      <div className="rounded-2xl border overflow-hidden" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
        <div className="px-6 py-4 border-b flex items-center justify-between" style={{ borderColor: '#E7E3DA' }}>
          <h2 className="text-sm font-semibold" style={{ color: '#1C3A56' }}>Cases</h2>
          <span className="text-xs" style={{ color: '#5B6470' }}>{cases.length} active</span>
        </div>
        <table className="w-full text-left">
          <thead>
            <tr className="border-b text-xs font-medium uppercase tracking-wide" style={{ borderColor: '#E7E3DA', color: '#5B6470' }}>
              <th className="py-3 px-6">Case</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Raters</th>
              <th className="py-3 px-4">Updated</th>
              <th className="py-3 px-4"></th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id} className="border-b last:border-0 hover:bg-[#FAF7F0] transition-colors" style={{ borderColor: '#E7E3DA' }}>
                <td className="py-4 px-6">
                  <p className="text-sm font-medium" style={{ color: '#1A1F26' }}>{c.display_name}</p>
                  <p className="text-xs mt-0.5 font-mono" style={{ color: '#5B6470' }}>{c.external_reference || '—'}</p>
                </td>
                <td className="py-4 px-4">
                  <span className="px-2.5 py-1 rounded-full text-xs font-medium" style={statusStyle(c.status)}>
                    {statusLabel(c.status)}
                  </span>
                </td>
                <td className="py-4 px-4">
                  <RaterDots raters={c.raters || { parent: false, teacher: false, adolescent: false }} />
                </td>
                <td className="py-4 px-4 text-xs" style={{ color: '#5B6470' }}>
                  {timeAgo(c.created_at)}
                </td>
                <td className="py-4 px-4">
                  <Link
                    href={`/cases/${c.id}`}
                    className="text-xs font-medium transition-colors hover:underline"
                    style={{ color: '#4C9A94' }}
                  >
                    Open →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {cases.length === 0 && (
          <div className="px-6 py-16 text-center">
            <p className="text-sm" style={{ color: '#5B6470' }}>Your caseload is clear.</p>
          </div>
        )}
      </div>

      {/* New Case Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl border" style={{ borderColor: '#E7E3DA' }}>
            <h3 className="text-lg font-semibold mb-1" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>New Case</h3>
            <p className="text-xs mb-5" style={{ color: '#5B6470' }}>A display name is used internally. Do not enter personally identifiable student information.</p>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5 uppercase tracking-wide" style={{ color: '#5B6470' }}>
                  Display Name
                </label>
                <input
                  type="text"
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
                  placeholder="e.g. Student A"
                  required
                  autoFocus
                  className="w-full px-3 py-2.5 rounded-lg border text-sm focus:outline-none"
                  style={{ borderColor: '#E7E3DA', color: '#1A1F26' }}
                />
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm rounded-lg"
                  style={{ color: '#5B6470' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium rounded-lg"
                  style={{ background: '#1C3A56', color: '#fff' }}
                >
                  Create Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
