import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../components/ui/Logo'
import { Sparkles } from '../components/ui/Sparkles'

type Choice = {
  id: string
  label: string
  correct: boolean
  illustration: 'ball' | 'cat'
}

const question = {
  prompt: 'Which word starts with',
  sound: '/b/',
  choices: [
    { id: 'ball', label: 'ball', correct: true, illustration: 'ball' },
    { id: 'cat', label: 'cat', correct: false, illustration: 'cat' },
  ] as Choice[],
}

function ChoiceArt({ type }: { type: Choice['illustration'] }) {
  if (type === 'ball') {
    return (
      <svg width="88" height="88" viewBox="0 0 72 72" aria-hidden="true">
        <circle cx="36" cy="36" r="28" fill="#f97316" />
        <circle cx="36" cy="36" r="28" fill="none" stroke="#111827" strokeWidth="2.5" />
        <path d="M36 8v56M8 36h56" stroke="#111827" strokeWidth="2" />
        <path d="M16 18c8 6 16 8 20 8s12-2 20-8" stroke="#111827" strokeWidth="2" fill="none" />
        <path d="M16 54c8-6 16-8 20-8s12 2 20 8" stroke="#111827" strokeWidth="2" fill="none" />
        <circle cx="36" cy="36" r="5" fill="#111827" />
      </svg>
    )
  }

  return (
    <svg width="88" height="88" viewBox="0 0 72 72" aria-hidden="true">
      <ellipse cx="36" cy="42" rx="22" ry="18" fill="#fbbf24" />
      <circle cx="22" cy="28" r="8" fill="#fbbf24" />
      <circle cx="50" cy="28" r="8" fill="#fbbf24" />
      <circle cx="28" cy="40" r="3.5" fill="#111827" />
      <circle cx="44" cy="40" r="3.5" fill="#111827" />
      <ellipse cx="36" cy="47" rx="4" ry="3" fill="#f97316" />
      <path d="M30 52c2.5 3 9.5 3 12 0" stroke="#111827" strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  )
}

export function Lesson() {
  const [selected, setSelected] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<'correct' | 'incorrect' | null>(null)

  function choose(choice: Choice) {
    setSelected(choice.id)
    setFeedback(choice.correct ? 'correct' : 'incorrect')
  }

  return (
    <main className="relative min-h-svh overflow-hidden bg-gradient-to-b from-[#eef9f8] via-white to-white">
      <div className="relative mx-auto flex min-h-svh w-full max-w-4xl flex-col px-6 py-5 lg:px-8">
        <header className="flex items-center justify-between">
          <Logo />
          <Link to="/onboarding/ready" className="text-sm font-bold text-navy hover:text-teal">
            ← Exit lesson
          </Link>
        </header>

        <div className="flex flex-1 flex-col items-center justify-center py-10">
          <div className="mb-6 flex items-center gap-2 text-sm font-bold text-slate-text">
            <span>Phonics: Letter Sounds</span>
            <span className="text-slate-300">•</span>
            <span>3 of 10</span>
          </div>

          <div className="w-full max-w-2xl rounded-[1.75rem] border border-slate-100 bg-white p-6 shadow-[0_20px_50px_rgba(15,31,58,0.1)] sm:p-8">
            <div className="mb-8 flex items-center justify-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-teal text-white">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M11 5L6 9H3v6h3l5 4V5z" fill="currentColor" />
                  <path d="M15.5 8.5a4.5 4.5 0 010 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <h1 className="relative text-2xl font-extrabold text-navy sm:text-3xl">
                {question.prompt}{' '}
                <span className="text-teal">{question.sound}</span>?
                <span className="absolute -right-6 -top-3">
                  <Sparkles />
                </span>
              </h1>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {question.choices.map((choice) => {
                const isSelected = selected === choice.id
                return (
                  <button
                    key={choice.id}
                    type="button"
                    onClick={() => choose(choice)}
                    className={`flex flex-col items-center rounded-2xl border-[2.5px] p-6 transition-all ${
                      isSelected
                        ? choice.correct
                          ? 'border-teal bg-teal-light/50'
                          : 'border-red-400 bg-red-50'
                        : 'border-slate-200 bg-white hover:border-teal/50'
                    }`}
                  >
                    <ChoiceArt type={choice.illustration} />
                    <span className="mt-3 text-xl font-extrabold text-navy">{choice.label}</span>
                    <span className="mt-2 text-xs font-bold text-slate-text">
                      Look {choice.id === 'ball' ? 'left' : 'right'} to select
                    </span>
                  </button>
                )
              })}
            </div>

            {feedback ? (
              <p
                className={`mt-6 text-center text-base font-extrabold ${
                  feedback === 'correct' ? 'text-teal' : 'text-red-500'
                }`}
              >
                {feedback === 'correct'
                  ? 'Nice work! Ball starts with /b/.'
                  : 'Not quite — try looking at the other choice.'}
              </p>
            ) : (
              <p className="mt-6 text-center text-sm font-semibold text-slate-text">
                Use eye movement to choose: look left or right, then hold steady.
              </p>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
