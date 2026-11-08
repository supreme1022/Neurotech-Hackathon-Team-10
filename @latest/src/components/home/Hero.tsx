import { Button } from '../ui/Button'
import { Sparkles } from '../ui/Sparkles'
import { Navbar } from './Navbar'

function HeroMockup() {
  return (
    <div className="relative mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">
      <div className="relative rounded-[1.75rem] border border-slate-100 bg-white p-5 shadow-[0_20px_50px_rgba(15,31,58,0.12)] sm:p-6">
        <div className="mb-5 flex items-center justify-between gap-4">
          <h3 className="text-base font-extrabold text-navy sm:text-lg">
            Phonics: Letter Sounds
          </h3>
          <div className="flex min-w-[7.5rem] flex-col items-end gap-1">
            <span className="text-xs font-semibold text-slate-text">3 of 10</span>
            <div className="h-2 w-full overflow-hidden rounded-full bg-sky">
              <div className="h-full w-[30%] rounded-full bg-[#3b82f6]" />
            </div>
          </div>
        </div>

        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-teal text-white">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M11 5L6 9H3v6h3l5 4V5z"
                fill="currentColor"
              />
              <path
                d="M15.5 8.5a4.5 4.5 0 010 7"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <p className="text-base font-bold text-navy sm:text-lg">
            Which word starts with <span className="text-teal">/b/</span>?
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          <div className="flex flex-col items-center rounded-2xl border-[2.5px] border-teal bg-teal-light/40 p-4 shadow-sm">
            <svg width="72" height="72" viewBox="0 0 72 72" aria-hidden="true">
              <circle cx="36" cy="36" r="28" fill="#f97316" />
              <circle cx="36" cy="36" r="28" fill="none" stroke="#111827" strokeWidth="2.5" />
              <path d="M36 8v56M8 36h56" stroke="#111827" strokeWidth="2" />
              <path
                d="M16 18c8 6 16 8 20 8s12-2 20-8"
                stroke="#111827"
                strokeWidth="2"
                fill="none"
              />
              <path
                d="M16 54c8-6 16-8 20-8s12 2 20 8"
                stroke="#111827"
                strokeWidth="2"
                fill="none"
              />
              <circle cx="36" cy="36" r="5" fill="#111827" />
            </svg>
            <span className="mt-2 text-lg font-extrabold text-navy">ball</span>
          </div>

          <div className="flex flex-col items-center rounded-2xl border-2 border-slate-200 bg-white p-4">
            <svg width="72" height="72" viewBox="0 0 72 72" aria-hidden="true">
              <ellipse cx="36" cy="42" rx="22" ry="18" fill="#fbbf24" />
              <circle cx="22" cy="28" r="8" fill="#fbbf24" />
              <circle cx="50" cy="28" r="8" fill="#fbbf24" />
              <circle cx="28" cy="40" r="3.5" fill="#111827" />
              <circle cx="44" cy="40" r="3.5" fill="#111827" />
              <ellipse cx="36" cy="47" rx="4" ry="3" fill="#f97316" />
              <path
                d="M30 52c2.5 3 9.5 3 12 0"
                stroke="#111827"
                strokeWidth="2"
                strokeLinecap="round"
                fill="none"
              />
              <path d="M34 47l-6 3M38 47l6 3" stroke="#f97316" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <span className="mt-2 text-lg font-extrabold text-navy">cat</span>
          </div>
        </div>
      </div>

      <Sparkles className="absolute -right-3 top-1/3 sm:-right-6" color="#14b8a6" />
    </div>
  )
}

const features = [
  {
    title: 'Audio-Guided Lessons',
    bg: 'bg-teal-light',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M4 10v4a2 2 0 002 2h1l3 3V5L7 8H6a2 2 0 00-2 2z"
          fill="#0f9e98"
        />
        <path d="M15 9a3 3 0 010 6M17.5 7a5.5 5.5 0 010 10" stroke="#0f9e98" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: 'Adaptive Learning',
    bg: 'bg-sky',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M13 2L4 14h7l-1 8 10-14h-7l0-6z" fill="#0f9e98" />
      </svg>
    ),
  },
  {
    title: 'Track Progress',
    bg: 'bg-mint',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="4" y="12" width="4" height="8" rx="1" fill="#8bc53f" />
        <rect x="10" y="8" width="4" height="12" rx="1" fill="#8bc53f" />
        <rect x="16" y="4" width="4" height="16" rx="1" fill="#8bc53f" />
      </svg>
    ),
  },
]

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-[#eef9f8] via-white to-white">
      <div
        className="pointer-events-none absolute -left-24 -top-20 h-72 w-72 rounded-full bg-[#c7ebe9]/70 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -right-16 top-40 h-80 w-80 rounded-full bg-[#d7f0ee]/80 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute bottom-24 left-1/3 h-48 w-48 rounded-full bg-[#e8f7e4]/60 blur-3xl"
        aria-hidden="true"
      />

      <Navbar />

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 pb-10 pt-8 lg:grid-cols-2 lg:gap-16 lg:px-8 lg:pb-14 lg:pt-12">
        <div className="max-w-xl text-left">
          <h1 className="text-4xl font-extrabold leading-[1.12] tracking-tight text-navy sm:text-5xl lg:text-[3.35rem]">
            Learn phonics{' '}
            <span className="relative inline-block">
              with your eyes.
              <span className="absolute -right-5 -top-3 sm:-right-6 sm:-top-4">
                <Sparkles />
              </span>
              <svg
                className="absolute -bottom-1 left-0 w-full"
                height="10"
                viewBox="0 0 220 10"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path
                  d="M2 7C40 2 80 8 110 5C150 1 190 8 218 4"
                  stroke="#8bc53f"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  fill="none"
                />
              </svg>
            </span>
          </h1>

          <p className="mt-6 max-w-md text-base leading-relaxed text-slate-text sm:text-lg">
            A hands-free, adaptive learning platform that helps every student
            build reading confidence.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button to="/get-started" variant="primary" className="px-7 py-3">
              Get Started
              <span aria-hidden="true">→</span>
            </Button>
            <Button variant="secondary" className="px-6 py-3">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
                <path d="M3 2.5v9l8-4.5L3 2.5z" />
              </svg>
              See How It Works
            </Button>
          </div>
        </div>

        <HeroMockup />
      </div>

      <div className="relative mx-auto max-w-6xl px-6 pb-12 lg:px-8 lg:pb-16">
        <div className="grid gap-6 border-t border-slate-200/80 pt-8 sm:grid-cols-3 sm:gap-0">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className={`flex items-center justify-center gap-3 sm:justify-start sm:px-6 ${
                index > 0 ? 'sm:border-l sm:border-slate-200' : ''
              }`}
            >
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${feature.bg}`}>
                {feature.icon}
              </div>
              <span className="text-sm font-extrabold text-navy sm:text-[0.95rem]">
                {feature.title}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
