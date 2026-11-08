import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DashboardShell } from '../../components/dashboard/DashboardShell'
import { studentNav } from '../../components/dashboard/navConfig'
import { TopBar } from '../../components/dashboard/TopBar'
import { Button } from '../../components/ui/Button'
import { Sparkles } from '../../components/ui/Sparkles'

const answers = ['15', '16', '17', '18']

export function LessonSession() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<string | null>(null)

  function selectAnswer(answer: string) {
    setSelected(answer)
    window.setTimeout(() => {
      navigate('/dashboard/lesson/feedback', { state: { answer } })
    }, 250)
  }

  return (
    <DashboardShell
      items={studentNav}
      topBar={
        <TopBar
          breadcrumb="Math > Addition & Subtraction"
          timer="06:24"
          showExit
          onExit={() => navigate('/dashboard/lessons')}
        />
      }
    >
      <div className="mb-5 rounded-2xl border border-slate-100 bg-white px-5 py-4 shadow-sm">
        <div className="mb-2 flex items-center justify-between text-sm font-bold text-navy">
          <span>Lesson Progress</span>
          <span>3 of 10</span>
        </div>
        <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
          <div className="h-full w-[30%] rounded-full bg-teal" />
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_220px]">
        <section className="rounded-[1.75rem] border border-slate-100 bg-white p-6 shadow-[0_16px_40px_rgba(15,31,58,0.06)] sm:p-8">
          <span className="inline-flex rounded-full bg-[#ede9fe] px-3 py-1 text-xs font-extrabold text-purple">
            Question 4
          </span>
          <h2 className="relative mt-5 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
            What is 12 + 5?
            <span className="absolute -top-3 left-[13.5rem] sm:left-[16.5rem]">
              <Sparkles />
            </span>
          </h2>

          <div className="mt-8 grid grid-cols-2 gap-4">
            {answers.map((answer) => {
              const isSelected = selected === answer
              return (
                <button
                  key={answer}
                  type="button"
                  onClick={() => selectAnswer(answer)}
                  className={`rounded-2xl border-[2.5px] px-4 py-8 text-3xl font-extrabold text-navy transition-all ${
                    isSelected
                      ? 'border-teal bg-teal-light ring-4 ring-teal/10'
                      : 'border-teal/40 bg-white hover:border-teal hover:bg-teal-light/40'
                  }`}
                >
                  {answer}
                </button>
              )
            })}
          </div>
        </section>

        <aside className="rounded-[1.5rem] border border-slate-100 bg-white p-5 shadow-sm">
          <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-2xl border-2 border-dashed border-teal/40 bg-teal-light">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="7" stroke="#0f9e98" strokeWidth="2" />
              <circle cx="12" cy="12" r="2.5" fill="#0f9e98" />
            </svg>
          </div>
          <p className="mt-4 text-center text-sm font-extrabold text-navy">Eye Tracking</p>
          <p className="mt-2 flex items-center justify-center gap-1.5 text-xs font-bold text-[#16a34a]">
            <span className="h-2 w-2 rounded-full bg-[#22c55e]" />
            Active
          </p>
          <div className="mt-6 rounded-xl bg-[#ede9fe] p-3 text-xs font-semibold leading-relaxed text-navy">
            <span className="mb-1 block font-extrabold text-purple">Tip</span>
            Keep your focus on an answer to select it.
          </div>
        </aside>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="ghost"
          className="border-teal text-teal hover:bg-teal-light"
          onClick={() => navigate('/dashboard/lessons')}
        >
          ← Back
        </Button>
        <Button
          variant="secondary"
          className="border-slate-200"
          onClick={() => navigate('/dashboard/lesson/feedback')}
        >
          Skip ≫
        </Button>
      </div>
    </DashboardShell>
  )
}
