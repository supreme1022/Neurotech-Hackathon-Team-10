import { useState } from 'react'
import { Link } from 'react-router-dom'
import { DashboardShell } from '../../components/dashboard/DashboardShell'
import { studentNav } from '../../components/dashboard/navConfig'
import { TopBar } from '../../components/dashboard/TopBar'
import { Button } from '../../components/ui/Button'
import { Sparkles } from '../../components/ui/Sparkles'

const subjects = [
  { id: 'math', label: 'Math', color: 'bg-[#ede9fe] text-purple', icon: '🧮' },
  { id: 'reading', label: 'Reading', color: 'bg-mint text-teal', icon: '📖' },
  { id: 'science', label: 'Science', color: 'bg-[#dbeafe] text-[#2563eb]', icon: '🧪' },
  { id: 'social', label: 'Social Studies', color: 'bg-[#fef3c7] text-[#ca8a04]', icon: '🌍' },
] as const

const lessonsBySubject: Record<string, Array<{ title: string; count: string; progress: number; icon: string }>> = {
  math: [
    { title: 'Addition & Subtraction', count: '3 lessons', progress: 67, icon: '＋' },
    { title: 'Multiplication Basics', count: '4 lessons', progress: 0, icon: '📊' },
    { title: 'Fractions', count: '3 lessons', progress: 0, icon: '◔' },
  ],
  reading: [
    { title: 'Letter Sounds', count: '5 lessons', progress: 65, icon: 'Aa' },
    { title: 'Sight Words', count: '4 lessons', progress: 20, icon: '👁' },
    { title: 'Blending', count: '3 lessons', progress: 0, icon: '🔗' },
  ],
  science: [
    { title: 'Plants', count: '3 lessons', progress: 40, icon: '🌱' },
    { title: 'Animals', count: '4 lessons', progress: 0, icon: '🐾' },
    { title: 'Weather', count: '2 lessons', progress: 0, icon: '☁' },
  ],
  social: [
    { title: 'Community Helpers', count: '3 lessons', progress: 10, icon: '🏘' },
    { title: 'Maps', count: '2 lessons', progress: 0, icon: '🗺' },
    { title: 'Cultures', count: '3 lessons', progress: 0, icon: '🌏' },
  ],
}

export function Lessons() {
  const [subject, setSubject] = useState<(typeof subjects)[number]['id']>('math')
  const lessons = lessonsBySubject[subject]
  const subjectLabel = subjects.find((item) => item.id === subject)?.label ?? 'Math'

  return (
    <DashboardShell
      items={studentNav}
      topBar={<TopBar userName="Learner" userInitial="L" />}
    >
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 text-center">
          <p className="text-xs font-extrabold tracking-[0.16em] text-teal uppercase">
            Choose a Subject
          </p>
          <h2 className="relative mt-3 inline-block text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
            Pick a subject to learn.
            <span className="absolute -right-6 -top-3">
              <Sparkles />
            </span>
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-base text-slate-text">
            Explore lessons, build your skills, and learn at your own pace.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {subjects.map((item) => {
            const selected = subject === item.id
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setSubject(item.id)}
                className={`rounded-[1.5rem] border-[2.5px] bg-white p-5 text-center shadow-sm transition-all ${
                  selected ? 'border-teal ring-4 ring-teal/10' : 'border-transparent hover:border-teal/30'
                }`}
              >
                <div className={`mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl text-2xl ${item.color}`}>
                  {item.icon}
                </div>
                <p className="text-sm font-extrabold text-navy">{item.label}</p>
              </button>
            )
          })}
        </div>

        <section className="mt-8 rounded-[1.75rem] border border-slate-100 bg-white p-5 shadow-sm sm:p-6">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-xl font-extrabold text-navy">{subjectLabel} Lessons</h3>
            <select className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-navy outline-none">
              <option>Grade 3</option>
              <option>Grade 2</option>
              <option>Grade 4</option>
            </select>
          </div>

          <div className="space-y-3">
            {lessons.map((lesson) => (
              <Link
                key={lesson.title}
                to="/dashboard/lesson"
                className="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-100 bg-page/70 px-4 py-4 transition-colors hover:border-teal/40 hover:bg-white"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-lg font-extrabold text-teal shadow-sm">
                  {lesson.icon}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-extrabold text-navy">{lesson.title}</p>
                  <p className="text-sm text-slate-text">{lesson.count}</p>
                </div>
                <div className="flex w-full items-center gap-3 sm:w-48">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-teal"
                      style={{ width: `${lesson.progress}%` }}
                    />
                  </div>
                  <span className="w-10 text-right text-xs font-bold text-navy">{lesson.progress}%</span>
                </div>
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-teal text-white">
                  ▶
                </span>
              </Link>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-center gap-2">
            {[0, 1, 2, 3].map((dot) => (
              <span
                key={dot}
                className={`h-2.5 w-2.5 rounded-full ${dot === 1 ? 'bg-teal' : 'bg-slate-300'}`}
              />
            ))}
          </div>
        </section>

        <div className="mt-6">
          <Button to="/dashboard" variant="ghost" className="border-teal text-teal hover:bg-teal-light">
            ← Back
          </Button>
        </div>
      </div>
    </DashboardShell>
  )
}
