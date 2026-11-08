import { Link } from 'react-router-dom'
import { DashboardShell } from '../../components/dashboard/DashboardShell'
import { studentHomeNav } from '../../components/dashboard/navConfig'
import { TopBar } from '../../components/dashboard/TopBar'
import { Button } from '../../components/ui/Button'

const exploreCards = [
  {
    title: 'Phonics',
    subtitle: 'Letters & sounds',
    to: '/dashboard/lessons',
    icon: (
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#dbeafe] text-sm font-extrabold text-[#2563eb]">
        abc
      </div>
    ),
  },
  {
    title: 'Word Reading',
    subtitle: 'Build new words',
    to: '/dashboard/lessons',
    icon: (
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#fef3c7] text-lg">
        📚
      </div>
    ),
  },
  {
    title: 'Listening',
    subtitle: 'Hear & understand',
    to: '/dashboard/lessons',
    icon: (
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-light text-teal">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 10v4a2 2 0 002 2h1l3 3V5L7 8H6a2 2 0 00-2 2z" fill="currentColor" />
          <path d="M15 9a3 3 0 010 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
    ),
  },
]

export function StudentDashboard() {
  return (
    <DashboardShell
      items={studentHomeNav}
      topBar={<TopBar showDeviceReady userName="Jordan" userInitial="J" />}
      sidebarFooter={
        <div className="rounded-2xl bg-teal-light p-4">
          <p className="text-sm font-extrabold text-navy">Need a little help?</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-text">
            Listen to instructions or ask a grown-up for support.
          </p>
          <a href="#help" className="mt-3 inline-flex items-center gap-1 text-sm font-bold text-teal">
            Help Center ↗
          </a>
        </div>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight text-navy">
                Hi, Jordan! <span aria-hidden="true">✨</span>
              </h2>
              <p className="mt-1 text-base text-slate-text">Ready to learn something new today?</p>
            </div>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#fef9c3] px-3 py-1.5 text-xs font-extrabold text-navy">
              + You&apos;re doing great!
            </span>
          </div>

          <section className="overflow-hidden rounded-[1.75rem] bg-gradient-to-br from-[#dbeafe] via-[#e0f2fe] to-[#ecfeff] p-6 shadow-[0_12px_30px_rgba(15,31,58,0.06)] sm:p-7">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-md">
                <p className="text-xs font-extrabold tracking-[0.12em] text-teal uppercase">
                  Pick up where you left off
                </p>
                <h3 className="mt-2 text-2xl font-extrabold text-navy">
                  Let&apos;s practice letter sounds
                </h3>
                <p className="mt-2 text-sm font-semibold text-slate-text">
                  Phonics · Beginning sounds · Lesson 3
                </p>
                <Button to="/dashboard/lesson" variant="primary" className="mt-5 px-6 py-3">
                  Continue Learning
                  <span aria-hidden="true">→</span>
                </Button>
                <div className="mt-5">
                  <div className="mb-1.5 flex items-center justify-between text-xs font-bold text-navy">
                    <span>Progress</span>
                    <span>65% complete</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-white/70">
                    <div className="h-full w-[65%] rounded-full bg-teal" />
                  </div>
                </div>
              </div>

              <div className="relative mx-auto w-40 rounded-2xl bg-white p-4 shadow-md sm:mx-0">
                <div className="absolute -top-2 -right-2 flex h-8 w-8 items-center justify-center rounded-full bg-[#22c55e] text-sm text-white">
                  ★
                </div>
                <div className="flex h-28 items-center justify-center rounded-xl bg-[#fee2e2] text-4xl">
                  📕
                </div>
                <p className="mt-3 text-center text-sm font-extrabold text-navy">ABC · Sounds</p>
              </div>
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="text-xl font-extrabold text-navy">Explore learning</h3>
              <Link to="/dashboard/lessons" className="text-sm font-bold text-teal hover:text-teal-dark">
                View all lessons →
              </Link>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {exploreCards.map((card) => (
                <Link
                  key={card.title}
                  to={card.to}
                  className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
                >
                  {card.icon}
                  <p className="mt-3 text-base font-extrabold text-navy">{card.title}</p>
                  <p className="mt-1 text-sm text-slate-text">{card.subtitle}</p>
                </Link>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-100 bg-white p-5">
            <h3 className="text-lg font-extrabold text-navy">A little practice every day</h3>
            <p className="mt-1 text-sm text-slate-text">
              Short lessons, steady progress, and plenty of chances to grow.
            </p>
          </section>
        </div>

        <aside className="space-y-4">
          <div className="rounded-[1.5rem] border border-slate-100 bg-white p-5 shadow-sm">
            <h3 className="text-base font-extrabold text-navy">Your progress</h3>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-page p-3">
                <p className="text-2xl font-extrabold text-navy">8</p>
                <p className="text-xs font-semibold text-slate-text">Lessons finished</p>
              </div>
              <div className="rounded-xl bg-page p-3">
                <p className="text-2xl font-extrabold text-navy">84%</p>
                <p className="text-xs font-semibold text-slate-text">Practice accuracy</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="mb-1.5 flex items-center justify-between text-xs font-bold text-navy">
                <span>Weekly goal</span>
                <span>3 of 5 lessons</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full w-[60%] rounded-full bg-teal" />
              </div>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-100 bg-white p-5 shadow-sm">
            <h3 className="text-base font-extrabold text-navy">Recommended for you</h3>
            <ul className="mt-4 space-y-3">
              <li className="flex gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-light text-teal">◎</span>
                <div>
                  <p className="text-sm font-extrabold text-navy">Beginning sounds</p>
                  <p className="text-xs text-slate-text">Practice words with B and D</p>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#ede9fe] text-purple">📢</span>
                <div>
                  <p className="text-sm font-extrabold text-navy">Listen & choose</p>
                  <p className="text-xs text-slate-text">5-minute audio practice</p>
                </div>
              </li>
            </ul>
          </div>

          <div className="rounded-[1.5rem] bg-mint p-5">
            <h3 className="text-base font-extrabold text-navy">
              Keep it up! <span aria-hidden="true">✨</span>
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-text">
              Every word you practice helps your reading skills grow.
            </p>
          </div>
        </aside>
      </div>
    </DashboardShell>
  )
}
