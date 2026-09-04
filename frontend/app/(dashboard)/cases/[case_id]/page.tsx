'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API = 'http://localhost:8000/api/v1';
const DIMS = ['Attention & Persistence', 'Activity', 'Adaptability', 'Sensitivity', 'Sociability', 'Self-Regulation'];

const MOCK_DIMENSIONS = [
  { label: 'Attention & Persistence', parent: 62, teacher: 88, adolescent: 55 },
  { label: 'Activity',               parent: 71, teacher: 74, adolescent: 68 },
  { label: 'Adaptability',           parent: 45, teacher: 43, adolescent: 49 },
  { label: 'Sensitivity',            parent: 80, teacher: 58, adolescent: 77 },
  { label: 'Sociability',            parent: 60, teacher: 63, adolescent: 61 },
  { label: 'Self-Regulation',        parent: 52, teacher: 89, adolescent: 50 },
];

const MOCK_SIGNALS = [
  { id: 'sig-1', title: 'Attention & Persistence', description: 'Parent–Teacher: Meaningful divergence (26 pt). Prototype visualization rule — not a validated clinical cutoff.', raterPair: 'Parent ↔ Teacher', signal_level: 'MEANINGFUL' },
  { id: 'sig-2', title: 'Self-Regulation',         description: 'Teacher–Adolescent: Meaningful divergence (39 pt). Prototype visualization rule — not a validated clinical cutoff.', raterPair: 'Teacher ↔ Adolescent', signal_level: 'MEANINGFUL' },
];

const MOCK_EVIDENCE = {
  signal: { title: 'Attention & Persistence', description: 'Parent–Teacher: Meaningful divergence' },
  raterPair: ['PARENT', 'TEACHER'],
  scores: { PARENT: 62, TEACHER: 88 },
  divergence: 26,
  calculation: { method: 'Absolute difference', version: 'v1.2.0' },
  source_items: [
    { question_code: 'ATP-01', question_text: 'Struggles to maintain focus on quiet tasks.', rater: 'PARENT', response: 3 },
    { question_code: 'ATP-01', question_text: 'Struggles to maintain focus on quiet tasks.', rater: 'TEACHER', response: 5 },
  ],
  evidence: [
    {
      evidence_code: 'EV-ATP-001',
      title: 'Cross-informant agreement in attention ratings: a meta-analysis',
      source: 'Achenbach et al. (2017) — Journal of Child Psychology',
      certainty: 'Very Low',
      association_value: 'r = 0.28 across 269 studies',
      limitation: 'Effect sizes vary substantially by rater pair and setting.',
    },
  ],
};

type Tab = 'heatmap' | 'signals' | 'insights' | 'review';

function cellBg(val: number | null | undefined) {
  if (val == null) return '#F4F2ED';
  if (val >= 75) return '#b8e0db';
  if (val >= 50) return '#DCE9F2';
  return '#E7E3DA';
}

function maxDivergence(row: { parent?: number | null; teacher?: number | null; adolescent?: number | null }) {
  const vals = [row.parent, row.teacher, row.adolescent].filter((v): v is number => v != null);
  if (vals.length < 2) return null;
  return Math.max(...vals.flatMap((a, i) => vals.slice(i + 1).map((b) => Math.abs(a - b))));
}

export default function CaseDetailPage({ params }: { params: { case_id: string } }) {
  const { case_id } = params;

  const [tab, setTab] = useState<Tab>('heatmap');
  const [dimensions, setDimensions] = useState(MOCK_DIMENSIONS);
  const [signals, setSignals] = useState(MOCK_SIGNALS);
  const [sessions, setSessions] = useState([
    { rater_type: 'Parent', status: 'SUBMITTED' },
    { rater_type: 'Teacher', status: 'SUBMITTED' },
    { rater_type: 'Adolescent', status: 'SUBMITTED' },
  ]);
  const [displayName, setDisplayName] = useState('Alex Morgan');
  const [ref, setRef] = useState('MF-0241');

  // Evidence drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeSignal, setActiveSignal] = useState<typeof MOCK_SIGNALS[0] | null>(null);

  // Review
  const [reviewAction, setReviewAction] = useState<'MONITOR' | 'REACH_OUT' | 'REFER'>('MONITOR');
  const [reviewNote, setReviewNote] = useState('');
  const [reviewSaved, setReviewSaved] = useState(false);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  // Heatmap hover
  const [hoveredCell, setHoveredCell] = useState<{ dim: string; rater: string; val: number } | null>(null);

  // Insights
  const [insights, setInsights] = useState<{ qualitative_synthesis: string; contextualized_discrepancies: string; note: string } | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('MindLens_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    Promise.all([
      fetch(`${API}/cases/${case_id}`, { headers }),
      fetch(`${API}/cases/${case_id}/sessions`, { headers }),
      fetch(`${API}/cases/${case_id}/signals`, { headers }),
      fetch(`${API}/cases/${case_id}/discrepancies`, { headers }),
    ]).then(async ([caseRes, sessRes, sigRes, discRes]) => {
      if (caseRes.ok) {
        const d = await caseRes.json();
        setDisplayName(d.case?.display_name ?? d.display_name ?? displayName);
        setRef(d.case?.external_reference ?? d.external_reference ?? ref);
      }
      if (sessRes.ok) {
        const s = await sessRes.json();
        if (Array.isArray(s)) setSessions(s);
      }
      if (sigRes.ok) {
        const s = await sigRes.json();
        if (Array.isArray(s) && s.length > 0) setSignals(s);
      }
      if (discRes.ok) {
        const disc = await discRes.json();
        const scores: { dimension_id: string; dimension_label: string; rater_type: string; score: number }[] = disc.scores ?? [];
        if (scores.length > 0) {
          const map: Record<string, { label: string; parent?: number; teacher?: number; adolescent?: number }> = {};
          scores.forEach((s) => {
            if (!map[s.dimension_id]) map[s.dimension_id] = { label: s.dimension_label || s.dimension_id };
            const rt = s.rater_type?.toLowerCase();
            if (rt === 'parent') map[s.dimension_id].parent = Math.round(s.score);
            if (rt === 'teacher') map[s.dimension_id].teacher = Math.round(s.score);
            if (rt === 'adolescent') map[s.dimension_id].adolescent = Math.round(s.score);
          });
          setDimensions(Object.values(map) as typeof MOCK_DIMENSIONS);
        }
      }
    }).catch(() => {});
  }, [case_id]);

  const openEvidence = (sig: typeof MOCK_SIGNALS[0]) => {
    setActiveSignal(sig);
    setDrawerOpen(true);
  };

  const handleReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setReviewSubmitting(true);
    const token = localStorage.getItem('MindLens_token');
    try {
      await fetch(`${API}/cases/${case_id}/review`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ action: reviewAction, note: reviewNote }),
      });
    } catch {}
    setReviewSaved(true);
    setReviewSubmitting(false);
  };

  const raterStatusColor = (status: string) =>
    status === 'SUBMITTED' ? '#4C9A94' : status === 'STARTED' ? '#1C3A56' : '#5B6470';

  const raterStatusDot = (status: string) =>
    status === 'SUBMITTED' ? '●' : status === 'STARTED' ? '◐' : '○';

  return (
    <div style={{ minHeight: '100vh', background: '#FAF7F0' }}>
      {/* Case header */}
      <div className="px-8 py-6 border-b" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
        <Link href="/dashboard" className="text-xs font-medium flex items-center gap-1 mb-4 w-fit" style={{ color: '#5B6470' }}>
          ← Overview
        </Link>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-semibold" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
                {displayName}
              </h1>
              <span className="px-2.5 py-1 rounded-full text-xs font-medium" style={{ background: '#DCE9F2', color: '#1C3A56' }}>
                Ready for Review
              </span>
            </div>
            <p className="text-xs mt-1 font-mono" style={{ color: '#5B6470' }}>{ref}</p>
          </div>
          {/* Rater status strip */}
          <div className="flex gap-5">
            {sessions.map((s) => (
              <div key={s.rater_type} className="flex flex-col items-center gap-1">
                <span className="text-base" style={{ color: raterStatusColor(s.status) }}>{raterStatusDot(s.status)}</span>
                <span className="text-xs font-medium" style={{ color: '#5B6470' }}>{s.rater_type}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-8 border-b flex gap-6" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
        {(['heatmap', 'signals', 'insights', 'review'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="py-3 text-sm font-medium border-b-2 transition-colors"
            style={{
              borderColor: tab === t ? '#1C3A56' : 'transparent',
              color: tab === t ? '#1C3A56' : '#5B6470',
            }}
          >
            {t === 'heatmap' ? 'Perspective Heatmap'
              : t === 'signals' ? `Surfaced Signals (${signals.length})`
              : t === 'insights' ? 'AI Insights ✨'
              : 'Review'}
          </button>
        ))}
      </div>

      <div className="px-8 py-8 max-w-6xl mx-auto">
        
        {/* RATER SESSIONS / QRS */}
        <div className="mb-12">
          <h2 className="text-base font-semibold mb-4" style={{ color: '#1C3A56' }}>Independent Intake Sessions</h2>
          <div className="grid grid-cols-3 gap-6">
            {sessions.map((s: any) => (
              <div key={s.rater_type} className="rounded-2xl border p-6 flex flex-col items-center shadow-sm" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                <h3 className="font-semibold text-lg uppercase tracking-wider mb-2" style={{ color: '#1C3A56' }}>{s.rater_type}</h3>
                <span className="text-xs font-bold uppercase tracking-wider mb-6 px-3 py-1 rounded-full" style={{ background: '#F4F2ED', color: raterStatusColor(s.status) }}>
                   {s.status}
                </span>
                
                {s.qr_payload ? (
                  <img src={s.qr_payload.qr_base64 || s.qr_payload} alt={`${s.rater_type} QR`} className="w-32 h-32 mb-6" />
                ) : (
                  <div className="w-32 h-32 mb-6 flex items-center justify-center rounded-lg border-2 border-dashed" style={{ borderColor: '#E7E3DA', background: '#FAF7F0' }}>
                    <span className="text-xs font-medium text-center px-4" style={{ color: '#5B6470' }}>QR Not Available<br/>(Link Expired or Submitted)</span>
                  </div>
                )}
                
                <div className="flex flex-col w-full gap-2 mt-auto">
                  <a href={s.intake_url} target="_blank" rel="noreferrer" className="text-xs font-medium text-center border py-2.5 rounded-full transition-colors" style={{ borderColor: '#E7E3DA', color: '#1C3A56' }}>
                    Open Link
                  </a>
                  <button onClick={() => {
                      if (s.intake_url) {
                        navigator.clipboard.writeText(s.intake_url);
                        alert('Link copied!');
                      }
                  }} className="text-xs font-medium text-center border py-2.5 rounded-full transition-colors" style={{ borderColor: '#E7E3DA', color: '#1C3A56' }}>
                    Copy Link
                  </button>
                  {s.qr_payload && (
                    <a href={s.qr_payload.qr_base64 || s.qr_payload} download={`${s.rater_type}_QR.png`} className="text-xs font-medium text-center border py-2.5 rounded-full transition-colors" style={{ borderColor: '#E7E3DA', color: '#1C3A56' }}>
                      Download QR
                    </a>
                  )}
                  <button onClick={async () => {
                     if (!confirm(`Are you sure you want to regenerate the link for ${s.rater_type}? The old one will be invalidated.`)) return;
                     const token = localStorage.getItem('MindLens_token');
                     await fetch(`${API}/cases/${case_id}/sessions/${s.session_id}/regenerate`, {
                         method: 'POST',
                         headers: { 'Authorization': `Bearer ${token}` }
                     });
                     window.location.reload();
                  }} className="text-xs font-medium text-center border py-2.5 rounded-full transition-colors mt-2" style={{ borderColor: '#FCA5A5', color: '#B91C1C', background: '#FEF2F2' }}>
                    Regenerate Link
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* HEATMAP TAB */}
        {tab === 'heatmap' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold" style={{ color: '#1C3A56' }}>Dimension Comparison</h2>
              <p className="text-xs" style={{ color: '#5B6470' }}>
                Prototype visualization rule — not a validated clinical cutoff
              </p>
            </div>
            <div className="rounded-2xl border p-6" style={{ borderColor: '#E7E3DA', background: '#fff', height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={dimensions}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E7E3DA" />
                  <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#5B6470' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: '#5B6470' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: '1px solid #E7E3DA', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', fontSize: '14px' }}
                    cursor={{ fill: '#F4F2ED' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                  <Bar dataKey="parent" name="Parent" fill="#1C3A56" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="teacher" name="Teacher" fill="#4C9A94" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="adolescent" name="Adolescent" fill="#C7C0DE" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* SIGNALS TAB */}
        {tab === 'signals' && (
          <div className="space-y-4">
            <div className="mb-4">
              <h2 className="text-base font-semibold" style={{ color: '#1C3A56' }}>Surfaced Signals</h2>
              <p className="text-xs mt-1" style={{ color: '#5B6470' }}>
                Meaningful divergence between rater pairs. This is not a risk score or diagnosis. Final interpretation remains with the counselor.
              </p>
            </div>
            {signals.length === 0 ? (
              <div className="rounded-2xl border py-16 text-center" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                <p className="text-sm" style={{ color: '#5B6470' }}>No meaningful divergence has been surfaced from the available responses.</p>
              </div>
            ) : signals.map((sig) => (
              <div key={sig.id} className="rounded-2xl border p-6 flex items-start justify-between gap-4" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                <div className="space-y-2 flex-grow">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs px-2.5 py-1 rounded-full font-medium" style={{ background: '#C7C0DE', color: '#1C3A56' }}>
                      Meaningful Divergence
                    </span>
                    <span className="text-xs" style={{ color: '#5B6470' }}>{sig.raterPair ?? ''}</span>
                  </div>
                  <h3 className="text-base font-semibold" style={{ color: '#1C3A56' }}>{sig.title}</h3>
                  <p className="text-sm" style={{ color: '#5B6470' }}>{sig.description}</p>
                </div>
                <button
                  onClick={() => openEvidence(sig)}
                  className="text-xs font-medium px-4 py-2 rounded-full border whitespace-nowrap transition-colors hover:bg-[#DCE9F2]"
                  style={{ borderColor: '#1C3A56', color: '#1C3A56' }}
                >
                  Why was this surfaced? →
                </button>
              </div>
            ))}
          </div>
        )}

        {/* INSIGHTS TAB */}
        {tab === 'insights' && (
          <div className="max-w-2xl">
            <div className="mb-6 flex justify-between items-center">
              <div>
                <h2 className="text-base font-semibold" style={{ color: '#1C3A56' }}>AI Assistant Insights</h2>
                <p className="text-xs mt-1" style={{ color: '#5B6470' }}>
                  Powered by Grok (simulated). Do not use for clinical diagnosis. 
                </p>
              </div>
              {!insights && !insightsLoading && (
                <button
                  onClick={async () => {
                    setInsightsLoading(true);
                    const token = localStorage.getItem('MindLens_token');
                    try {
                      const res = await fetch(`${API}/cases/${case_id}/insights`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                      });
                      if(res.ok) setInsights(await res.json());
                    } catch(e) {}
                    setInsightsLoading(false);
                  }}
                  className="px-4 py-2 text-sm font-medium rounded-full"
                  style={{ background: '#1C3A56', color: '#fff' }}
                >
                  Generate Insights ✨
                </button>
              )}
            </div>
            
            {insightsLoading && (
              <div className="rounded-2xl border p-12 text-center" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                <p className="text-sm font-medium animate-pulse" style={{ color: '#1C3A56' }}>Analyzing clinical responses...</p>
              </div>
            )}
            
            {insights && (
              <div className="space-y-6">
                <div className="rounded-2xl border p-6" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                  <h3 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: '#4C9A94' }}>Qualitative Insight Synthesis</h3>
                  <p className="text-sm leading-relaxed" style={{ color: '#1A1F26' }}>{insights.qualitative_synthesis}</p>
                </div>
                <div className="rounded-2xl border p-6" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                  <h3 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: '#4C9A94' }}>Contextualizing Discrepancies</h3>
                  <p className="text-sm leading-relaxed" style={{ color: '#1A1F26' }}>{insights.contextualized_discrepancies}</p>
                </div>
                <p className="text-xs text-right italic" style={{ color: '#5B6470' }}>{insights.note}</p>
              </div>
            )}
          </div>
        )}

        {/* REVIEW TAB */}
        {tab === 'review' && (
          <div className="max-w-xl">
            <div className="mb-6">
              <h2 className="text-base font-semibold" style={{ color: '#1C3A56' }}>Counselor Review</h2>
              <p className="text-xs mt-1" style={{ color: '#5B6470' }}>
                MindLens does not make clinical recommendations. Select an action based on your professional judgment and the available evidence.
              </p>
            </div>

            {reviewSaved ? (
              <div className="rounded-2xl border p-6 space-y-4" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                <p className="text-sm font-medium" style={{ color: '#1C3A56' }}>Review Recorded</p>
                <div className="space-y-2 text-sm" style={{ color: '#5B6470' }}>
                  <p>Action: <span className="font-semibold" style={{ color: '#1A1F26' }}>{reviewAction.replace('_', ' ')}</span></p>
                  {reviewNote && <p className="italic">"{reviewNote}"</p>}
                  <p className="text-xs font-mono" style={{ color: '#5B6470' }}>
                    Audit timestamp: {new Date().toLocaleString()}
                  </p>
                </div>
                <button onClick={() => setReviewSaved(false)} className="text-xs" style={{ color: '#4C9A94' }}>Edit review</button>
              </div>
            ) : (
              <form onSubmit={handleReview} className="space-y-6">
                {/* Three equal action buttons — none preselected visually */}
                <div>
                  <label className="block text-xs font-medium uppercase tracking-wide mb-3" style={{ color: '#5B6470' }}>
                    Clinical Action
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['MONITOR', 'REACH_OUT', 'REFER'] as const).map((act) => (
                      <button
                        key={act}
                        type="button"
                        onClick={() => setReviewAction(act)}
                        className="py-4 rounded-xl border text-sm font-medium transition-all"
                        style={{
                          background: reviewAction === act ? '#1C3A56' : '#fff',
                          color: reviewAction === act ? '#fff' : '#1C3A56',
                          borderColor: reviewAction === act ? '#1C3A56' : '#E7E3DA',
                        }}
                      >
                        {act.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wide mb-2" style={{ color: '#5B6470' }}>
                    Counselor Note
                  </label>
                  <textarea
                    rows={5}
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                    placeholder="Record your clinical rationale, observations, or planned follow-up steps..."
                    className="w-full px-4 py-3 rounded-xl border text-sm focus:outline-none resize-none"
                    style={{ borderColor: '#E7E3DA', color: '#1A1F26', background: '#fff' }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  className="w-full py-3 rounded-full text-sm font-medium transition-colors"
                  style={{ background: '#1C3A56', color: '#fff' }}
                >
                  {reviewSubmitting ? 'Saving…' : 'Save Review'}
                </button>

                <p className="text-xs text-center" style={{ color: '#5B6470' }}>
                  MindLens is a decision-support prototype. It does not diagnose or predict individual risk. Final interpretation remains with a qualified professional.
                </p>
              </form>
            )}
          </div>
        )}
      </div>

      {/* EVIDENCE DRAWER */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end" style={{ background: 'rgba(28,58,86,0.25)' }}>
          <div className="h-full w-full max-w-lg overflow-y-auto flex flex-col" style={{ background: '#FAF7F0' }}>
            {/* Drawer header */}
            <div className="flex items-center justify-between px-6 py-5 border-b sticky top-0 z-10" style={{ borderColor: '#E7E3DA', background: '#FAF7F0' }}>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: '#5B6470' }}>Evidence Chain</p>
                <h3 className="text-base font-semibold" style={{ color: '#1C3A56' }}>{activeSignal?.title}</h3>
              </div>
              <button onClick={() => setDrawerOpen(false)} className="text-xl" style={{ color: '#5B6470' }}>✕</button>
            </div>

            <div className="px-6 py-6 space-y-6 flex-grow">
              {/* Step-by-step chain */}
              {[
                { step: '01', label: 'Rater Pair', content: MOCK_EVIDENCE.raterPair.join(' ↔ ') },
                { step: '02', label: 'Dimension', content: MOCK_EVIDENCE.signal.title },
                { step: '03', label: 'Scores', content: Object.entries(MOCK_EVIDENCE.scores).map(([k, v]) => `${k}: ${v}/100`).join('  ·  ') },
                { step: '04', label: 'Divergence', content: `${MOCK_EVIDENCE.divergence} pts · Prototype threshold — not a validated clinical cutoff` },
                { step: '05', label: 'Calculation', content: `${MOCK_EVIDENCE.calculation.method} · ${MOCK_EVIDENCE.calculation.version}` },
              ].map(({ step, label, content }) => (
                <div key={step} className="flex gap-4">
                  <span className="text-xs font-semibold w-6 shrink-0 mt-0.5" style={{ color: '#C7C0DE' }}>{step}</span>
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: '#5B6470' }}>{label}</p>
                    <p className="text-sm" style={{ color: '#1A1F26' }}>{content}</p>
                  </div>
                </div>
              ))}

              <div className="border-t pt-4" style={{ borderColor: '#E7E3DA' }}>
                <p className="text-xs font-medium uppercase tracking-wide mb-3" style={{ color: '#5B6470' }}>Source Items</p>
                {MOCK_EVIDENCE.source_items.map((item, i) => (
                  <div key={i} className="rounded-xl border p-4 mb-3 text-sm" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                    <p className="text-xs font-semibold uppercase mb-1" style={{ color: '#4C9A94' }}>{item.rater}</p>
                    <p style={{ color: '#1A1F26' }}>{item.question_text}</p>
                    <p className="mt-1 text-xs" style={{ color: '#5B6470' }}>
                      Response: <span className="font-semibold" style={{ color: '#1C3A56' }}>{item.response}</span>/5
                    </p>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4" style={{ borderColor: '#E7E3DA' }}>
                <p className="text-xs font-medium uppercase tracking-wide mb-3" style={{ color: '#5B6470' }}>Research Evidence</p>
                {MOCK_EVIDENCE.evidence.map((ev) => (
                  <div key={ev.evidence_code} className="rounded-xl border p-4 space-y-2 text-sm" style={{ borderColor: '#E7E3DA', background: '#fff' }}>
                    <p className="font-semibold" style={{ color: '#1C3A56' }}>{ev.title}</p>
                    <p className="text-xs italic" style={{ color: '#5B6470' }}>{ev.source}</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs" style={{ color: '#5B6470' }}>
                      <span>Certainty: <b style={{ color: '#1A1F26' }}>{ev.certainty}</b></span>
                      {ev.association_value && <span>{ev.association_value}</span>}
                    </div>
                    {ev.limitation && (
                      <p className="text-xs rounded-lg px-3 py-2" style={{ background: '#E7E3DA', color: '#5B6470' }}>
                        Limitation: {ev.limitation}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <p className="text-xs text-center pb-4" style={{ color: '#5B6470' }}>
                MindLens is a decision-support prototype. It does not diagnose or predict individual risk. Final interpretation remains with a qualified professional.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
