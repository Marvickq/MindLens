'use client';

import React, { useEffect, useState } from 'react';

const MOCK_QUESTIONS = [
  { id: 'q1', text: 'Struggles to maintain focus on quiet or detailed tasks.' },
  { id: 'q2', text: 'Displays high physical energy or restlessness during structured activities.' },
  { id: 'q3', text: 'Adapts easily to sudden changes in schedule or routine.' },
  { id: 'q4', text: 'Reacts strongly to mild environmental or social stressors.' },
  { id: 'q5', text: 'Engages comfortably in new social situations.' },
  { id: 'q6', text: 'Has difficulty managing strong emotions when frustrated.' },
];

const RESPONSE_LABELS = ['Never', 'Rarely', 'Sometimes', 'Often', 'Almost Always'];

type Screen = 'landing' | 'intro' | 'question' | 'submit' | 'thankyou';

export default function PublicIntakePage({ params }: { params: { token: string } }) {
  const { token } = params;

  const [screen, setScreen] = useState<Screen>('landing');
  const [raterType, setRaterType] = useState('');
  const [questions, setQuestions] = useState(MOCK_QUESTIONS);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`http://localhost:8000/api/v1/intake/${token}`)
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then((d) => {
        setRaterType((d.rater_type ?? 'RESPONDENT').toLowerCase());
        if (Array.isArray(d.questions) && d.questions.length > 0) {
          setQuestions(d.questions.map((q: any) => ({ id: q.id, text: q.text || q.question_text })));
          const init: Record<string, number> = {};
          d.questions.forEach((q: any) => { if (q.saved_value) init[q.id] = q.saved_value; });
          setAnswers(init);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  const total = questions.length;
  const answered = Object.keys(answers).length;
  const q = questions[currentIdx];
  const pct = total > 0 ? Math.round((currentIdx / total) * 100) : 0;

  const selectAnswer = async (val: number) => {
    const newAnswers = { ...answers, [q.id]: val };
    setAnswers(newAnswers);
    setSaving(true);
    try {
      await fetch(`http://localhost:8000/api/v1/intake/${token}/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: q.id, value: val }),
      });
    } catch {}
    setSaving(false);
    // Auto-advance to next
    setTimeout(() => {
      if (currentIdx < total - 1) {
        setCurrentIdx(currentIdx + 1);
      } else {
        setScreen('submit');
      }
    }, 300);
  };

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await fetch(`http://localhost:8000/api/v1/intake/${token}/submit`, { method: 'POST' });
    } catch {}
    setSaving(false);
    setScreen('thankyou');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#FAF7F0' }}>
        <div className="text-sm" style={{ color: '#5B6470' }}>Loading…</div>
      </div>
    );
  }

  // LANDING SCREEN
  if (screen === 'landing') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16" style={{ background: '#FAF7F0' }}>
        <div className="max-w-sm w-full text-center space-y-6">
          <p className="text-sm font-semibold" style={{ color: '#1C3A56' }}>MindLens</p>
          <h1 className="text-2xl font-medium" style={{ color: '#1A1F26', fontFamily: 'Newsreader, serif' }}>
            You have been invited to share your observations.
          </h1>
          <p className="text-sm leading-relaxed" style={{ color: '#5B6470' }}>
            This takes about 5–10 minutes. Your responses are private and will only be seen by the school counselor coordinating this assessment.
          </p>
          <button
            onClick={() => setScreen('intro')}
            className="w-full py-3 rounded-full text-sm font-medium transition-colors"
            style={{ background: '#1C3A56', color: '#fff' }}
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

  // INTRO SCREEN
  if (screen === 'intro') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16" style={{ background: '#FAF7F0' }}>
        <div className="max-w-sm w-full space-y-6">
          <h2 className="text-xl font-medium" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
            Before you begin
          </h2>
          <ul className="space-y-3 text-sm" style={{ color: '#5B6470' }}>
            <li className="flex gap-3">
              <span style={{ color: '#4C9A94' }}>—</span>
              There are no right or wrong answers.
            </li>
            <li className="flex gap-3">
              <span style={{ color: '#4C9A94' }}>—</span>
              Rate each statement based on what you have observed recently.
            </li>
            <li className="flex gap-3">
              <span style={{ color: '#4C9A94' }}>—</span>
              Your responses are not visible to other people filling in this assessment.
            </li>
            <li className="flex gap-3">
              <span style={{ color: '#4C9A94' }}>—</span>
              Your progress is saved automatically after each question.
            </li>
          </ul>
          <button
            onClick={() => setScreen('question')}
            className="w-full py-3 rounded-full text-sm font-medium transition-colors"
            style={{ background: '#1C3A56', color: '#fff' }}
          >
            Start — {total} questions
          </button>
        </div>
      </div>
    );
  }

  // QUESTION SCREEN
  if (screen === 'question' && q) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: '#FAF7F0' }}>
        {/* Progress bar */}
        <div className="h-1 w-full" style={{ background: '#E7E3DA' }}>
          <div
            className="h-1 transition-all duration-500"
            style={{ width: `${pct}%`, background: '#4C9A94' }}
          />
        </div>

        <div className="flex-grow flex flex-col items-center justify-center px-6 py-12">
          <div className="max-w-sm w-full space-y-8">
            {/* Progress indicator */}
            <p className="text-xs text-center font-medium" style={{ color: '#5B6470' }}>
              {currentIdx + 1} of {total}
            </p>

            {/* Question */}
            <p className="text-lg text-center leading-snug font-medium" style={{ color: '#1A1F26', fontFamily: 'Newsreader, serif' }}>
              {q.text}
            </p>

            {/* Response options */}
            <div className="space-y-2">
              {RESPONSE_LABELS.map((label, i) => {
                const val = i + 1;
                const selected = answers[q.id] === val;
                return (
                  <button
                    key={val}
                    onClick={() => selectAnswer(val)}
                    className="w-full py-3 px-5 rounded-xl text-sm font-medium text-left transition-all border"
                    style={{
                      background: selected ? '#1C3A56' : '#fff',
                      color: selected ? '#fff' : '#1A1F26',
                      borderColor: selected ? '#1C3A56' : '#E7E3DA',
                    }}
                  >
                    {label}
                  </button>
                );
              })}
            </div>

            {/* Back nav */}
            {currentIdx > 0 && (
              <button
                onClick={() => setCurrentIdx(currentIdx - 1)}
                className="w-full text-center text-xs"
                style={{ color: '#5B6470' }}
              >
                ← Previous question
              </button>
            )}
          </div>
        </div>

        {saving && (
          <p className="text-center pb-4 text-xs" style={{ color: '#5B6470' }}>Saving…</p>
        )}
      </div>
    );
  }

  // SUBMIT SCREEN
  if (screen === 'submit') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16" style={{ background: '#FAF7F0' }}>
        <div className="max-w-sm w-full text-center space-y-6">
          <h2 className="text-xl font-medium" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
            All questions answered.
          </h2>
          <p className="text-sm" style={{ color: '#5B6470' }}>
            You answered {answered} of {total} questions. When you submit, your responses will be locked.
          </p>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="w-full py-3 rounded-full text-sm font-medium"
            style={{ background: '#1C3A56', color: '#fff' }}
          >
            {saving ? 'Submitting…' : 'Submit'}
          </button>
          <button
            onClick={() => { setCurrentIdx(total - 1); setScreen('question'); }}
            className="w-full text-xs"
            style={{ color: '#5B6470' }}
          >
            ← Review answers
          </button>
        </div>
      </div>
    );
  }

  // THANK YOU SCREEN
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16" style={{ background: '#FAF7F0' }}>
      <div className="max-w-sm w-full text-center space-y-6">
        <div className="w-12 h-12 rounded-full mx-auto flex items-center justify-center" style={{ background: '#DCE9F2' }}>
          <span style={{ color: '#4C9A94', fontSize: '1.25rem' }}>✓</span>
        </div>
        <h2 className="text-xl font-medium" style={{ color: '#1C3A56', fontFamily: 'Newsreader, serif' }}>
          Thank you for your time.
        </h2>
        <p className="text-sm leading-relaxed" style={{ color: '#5B6470' }}>
          Your responses have been securely recorded. They will be reviewed by the school counselor as part of a multi-perspective assessment. You may close this window.
        </p>
      </div>
    </div>
  );
}
