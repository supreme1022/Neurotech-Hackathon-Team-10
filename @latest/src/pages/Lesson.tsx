import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../components/ui/Logo'
import { Sparkles } from '../components/ui/Sparkles'
import timingsCsv from '../../../timings.csv?raw'
import { getPlayback, parseTimings } from '../lessonTimeline'

const intervals = parseTimings(timingsCsv)
const playbackDuration = intervals[intervals.length - 1].end

type Choice = {
  id: string
  label: string
  correct: boolean
  illustration: 'ball' | 'cat' | 'dog' | 'sun' | 'fish'
}

const questions = [{
  prompt: 'Which word starts with',
  sound: '/b/',
  choices: [
    { id: 'ball', label: 'ball', correct: true, illustration: 'ball' },
    { id: 'cat', label: 'cat', correct: false, illustration: 'cat' },
  ] as Choice[],
}, ...[
  { sound: '/k/', answer: 'cat', other: 'ball' },
  { sound: '/d/', answer: 'dog', other: 'sun' },
  { sound: '/s/', answer: 'sun', other: 'fish' },
  { sound: '/f/', answer: 'fish', other: 'dog' },
].map(({ sound, answer, other }, index) => ({
  prompt: 'Which word starts with',
  sound,
  choices: (index % 2 === 0 ? [other, answer] : [answer, other]).map((word) => ({
    id: word,
    label: word,
    correct: word === answer,
    illustration: word as Choice['illustration'],
  })),
}))]

function ChoiceArt({ type }: { type: Choice['illustration'] }) {
  if (type === 'dog' || type === 'sun' || type === 'fish') {
    return (
      <span className="flex h-[88px] w-[88px] items-center justify-center text-6xl" aria-hidden="true">
        {{ dog: '🐶', sun: '☀️', fish: '🐟' }[type]}
      </span>
    )
  }
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
  const [run, setRun] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const { questionIndex, complete, active, finished } = getPlayback(
    intervals, elapsed, questions.map((question) => question.choices[0].correct ? 'LEFT' : 'RIGHT'),
  )
  const question = questions[Math.min(questionIndex, questions.length - 1)]
  const selected = run === 0 || active?.direction === 'CENTER' || !active
    ? null : question.choices[active.direction === 'LEFT' ? 0 : 1]
  const feedback = selected ? (selected.correct ? 'correct' : 'incorrect') : null

  useEffect(() => {
    if (run === 0) return
    const start = performance.now()
    let frame: number
    function tick() {
      const seconds = Math.min((performance.now() - start) / 1000, playbackDuration)
      setElapsed(seconds)
      if (seconds < playbackDuration) frame = window.requestAnimationFrame(tick)
    }
    frame = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(frame)
  }, [run])

  function startDemo() {
    setElapsed(0)
    setRun((value) => value + 1)
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
            <span>{complete ? questions.length : questionIndex + 1} of {questions.length}</span>
          </div>

          <div className="mb-6 flex flex-col items-center gap-3">
            <p className="text-sm font-semibold text-slate-text" role="status">
              {run === 0 ? 'Start the demo when your recording reaches 8 seconds.'
                : finished ? 'Demo finished.' : `Demo playing · ${elapsed.toFixed(1)} / ${playbackDuration} seconds`}
            </p>
            <button type="button" onClick={startDemo} className="rounded-full bg-teal px-6 py-3 font-bold text-white">
              {run === 0 ? 'Start demo' : 'Restart demo'}
            </button>
          </div>

          {complete ? (
            <div className="w-full max-w-2xl rounded-[1.75rem] bg-white p-8 text-center shadow-lg" role="status">
              <h1 className="text-3xl font-extrabold text-navy">Lesson complete!</h1>
              <p className="mt-4 text-slate-text">Nice work! You answered all {questions.length} questions.</p>
              <button
                type="button"
                className="mt-6 rounded-full bg-teal px-6 py-3 font-bold text-white"
                onClick={startDemo}
              >
                Practice again
              </button>
            </div>
          ) : (
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

            <div className="grid grid-cols-2 gap-4">
              {question.choices.map((choice, index) => {
                const isSelected = selected?.id === choice.id
                return (
                  <button
                    key={choice.id}
                    type="button"
                    disabled
                    aria-pressed={isSelected}
                    className={`flex flex-col items-center rounded-2xl border-[2.5px] p-3 sm:p-6 ${
                      isSelected
                        ? choice.correct
                          ? 'border-teal bg-teal-light/50'
                          : 'border-red-400 bg-red-50'
                        : 'border-slate-200 bg-white'
                    }`}
                  >
                    <ChoiceArt type={choice.illustration} />
                    <span className="mt-3 text-xl font-extrabold text-navy">{choice.label}</span>
                    <span className="mt-2 text-xs font-bold text-slate-text">
                      Look {index === 0 ? 'left' : 'right'} to select
                    </span>
                  </button>
                )
              })}
            </div>

            {feedback ? (
              <p
                role="status"
                className={`mt-6 text-center text-base font-extrabold ${
                  feedback === 'correct' ? 'text-teal' : 'text-red-500'
                }`}
              >
                {feedback === 'correct'
                  ? `Nice work! ${selected?.label} starts with ${question.sound}. Continuing when this hold ends.`
                  : 'Not quite — this question will stay until a correct hold finishes.'}
              </p>
            ) : (
              <p className="mt-6 text-center text-sm font-semibold text-slate-text">
                {finished ? 'Playback has stopped. Restart the demo to replay the timings.'
                  : 'Look left or right to select. Centered gaze leaves both options clear.'}
              </p>
            )}
          </div>
          )}
        </div>
      </div>
    </main>
  )
}
