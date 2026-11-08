import { useState } from 'react'
import { InfoPanel } from '../components/onboarding/InfoPanel'
import { OnboardingFooter } from '../components/onboarding/OnboardingFooter'
import { OnboardingShell } from '../components/onboarding/OnboardingShell'
import { OnboardingStepper } from '../components/onboarding/OnboardingStepper'
import { Sparkles } from '../components/ui/Sparkles'

const grades = ['Pre-K', 'K', '1st', '2nd', '3rd', '4th', '5th'] as const

const learningGoals = [
  {
    id: 'letter-sounds',
    label: 'Build letter sound skills',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M5 5h6v14H7a2 2 0 01-2-2V5z" fill="#0f9e98" opacity="0.85" />
        <path d="M13 5h6v12a2 2 0 01-2 2h-4V5z" fill="#14b8a6" />
      </svg>
    ),
  },
  {
    id: 'word-reading',
    label: 'Improve word reading',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="5" y="14" width="14" height="3.5" rx="1" fill="#0f9e98" />
        <rect x="7" y="9.5" width="10" height="3.5" rx="1" fill="#0f9e98" opacity="0.75" />
        <rect x="9" y="5" width="6" height="3.5" rx="1" fill="#0f9e98" opacity="0.5" />
      </svg>
    ),
  },
  {
    id: 'listening',
    label: 'Strengthen listening & focus',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M4 10v4a2 2 0 002 2h1l3 3V5L7 8H6a2 2 0 00-2 2z" fill="#0f9e98" />
        <path d="M15 9a3 3 0 010 6M17.5 7a5.5 5.5 0 010 10" stroke="#0f9e98" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'confidence',
    label: 'Build reading confidence',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="4" y="13" width="4" height="7" rx="1" fill="#0f9e98" />
        <rect x="10" y="9" width="4" height="11" rx="1" fill="#0f9e98" />
        <rect x="16" y="5" width="4" height="15" rx="1" fill="#0f9e98" />
      </svg>
    ),
  },
]

const supportOptions = [
  'ADHD support',
  'Dyslexia-friendly pacing',
  'Limited mobility',
  'Speech impairment',
  'English language learner',
  'Prefer audio instructions',
]

function ProfileIllustration() {
  return (
    <svg width="160" height="110" viewBox="0 0 160 110" fill="none" aria-hidden="true">
      <ellipse cx="80" cy="88" rx="46" ry="10" fill="#b6e7e3" />
      <path d="M48 78c0-18 14-28 32-28s32 10 32 28" fill="#c4b5fd" />
      <path d="M52 78c4-12 14-18 28-18s24 6 28 18" fill="#a78bfa" />
      <path d="M58 78h44v4a8 8 0 01-8 8H66a8 8 0 01-8-8v-4z" fill="#8b5cf6" />
      <path
        d="M55 42c0-10 8-18 18-18h14c10 0 18 8 18 18v8c0 3-2 6-5 7l-4 2v6H64v-6l-4-2c-3-1-5-4-5-7v-8z"
        stroke="#0f9e98"
        strokeWidth="4"
        fill="#ccfbf1"
      />
      <path d="M55 48H46c-3 0-5 2-5 5v6c0 3 2 5 5 5h9" stroke="#0f9e98" strokeWidth="4" strokeLinecap="round" />
      <path d="M105 48h9c3 0 5 2 5 5v6c0 3-2 5-5 5h-9" stroke="#0f9e98" strokeWidth="4" strokeLinecap="round" />
      <path d="M118 28l4-6M124 32l7-2M116 22l1-6" stroke="#f5c518" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M36 34l-3-5M30 38l-6-1M38 28l-1-5" stroke="#7c6cf0" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

export function LearningProfile() {
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [grade, setGrade] = useState<(typeof grades)[number]>('Pre-K')
  const [goals, setGoals] = useState<string[]>(['letter-sounds'])
  const [support, setSupport] = useState('')

  function toggleGoal(id: string) {
    setGoals((current) =>
      current.includes(id) ? current.filter((goal) => goal !== id) : [...current, id],
    )
  }

  return (
    <OnboardingShell>
      <div className="mb-8 text-center">
        <p className="text-xs font-extrabold tracking-[0.16em] text-teal uppercase">
          Set up your learning profile
        </p>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
          Tell us about the learner
          <span className="relative inline-block">
            .
            <span className="absolute -right-5 -top-4">
              <Sparkles />
            </span>
          </span>
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-base text-slate-text">
          This helps PhoniFide personalize lessons for the best learning experience.
        </p>
      </div>

      <div className="grid flex-1 gap-6 lg:grid-cols-[220px_minmax(0,1fr)_240px] xl:grid-cols-[240px_minmax(0,1fr)_260px]">
        <OnboardingStepper currentStep="profile" />

        <section className="rounded-[1.75rem] border border-slate-100 bg-white p-6 shadow-[0_16px_40px_rgba(15,31,58,0.06)] sm:p-8">
          <form className="space-y-6" onSubmit={(event) => event.preventDefault()}>
            <label className="block">
              <span className="mb-2 block text-sm font-extrabold text-navy">Learner&apos;s Name</span>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-text">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="2" />
                    <path d="M5 19c1.2-3.5 4-5 7-5s5.8 1.5 7 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </span>
                <input
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Enter name"
                  className="w-full rounded-xl border border-slate-200 bg-white py-3 pr-4 pl-11 text-sm font-semibold text-navy outline-none placeholder:font-medium placeholder:text-slate-text/70 focus:border-teal focus:ring-2 focus:ring-teal/20"
                />
              </div>
            </label>

            <label className="block max-w-xs">
              <span className="mb-2 block text-sm font-extrabold text-navy">Age</span>
              <select
                value={age}
                onChange={(event) => setAge(event.target.value)}
                className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-navy outline-none focus:border-teal focus:ring-2 focus:ring-teal/20"
              >
                <option value="">Select age</option>
                {Array.from({ length: 14 }, (_, index) => index + 5).map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <fieldset>
              <legend className="mb-3 text-sm font-extrabold text-navy">Grade Level</legend>
              <div className="flex flex-wrap gap-2">
                {grades.map((option) => {
                  const selected = grade === option
                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setGrade(option)}
                      className={`rounded-full px-4 py-2 text-sm font-bold transition-colors ${
                        selected
                          ? 'border-2 border-teal bg-teal-light text-navy'
                          : 'border border-slate-200 bg-white text-navy hover:border-teal/50'
                      }`}
                    >
                      {option}
                    </button>
                  )
                })}
              </div>
            </fieldset>

            <fieldset>
              <legend className="mb-3 text-sm font-extrabold text-navy">Learning Goals</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                {learningGoals.map((goal) => {
                  const selected = goals.includes(goal.id)
                  return (
                    <button
                      key={goal.id}
                      type="button"
                      onClick={() => toggleGoal(goal.id)}
                      className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-left transition-colors ${
                        selected
                          ? 'border-teal bg-teal-light/50'
                          : 'border-slate-200 bg-white hover:border-teal/40'
                      }`}
                    >
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white shadow-sm">
                        {goal.icon}
                      </span>
                      <span className="flex-1 text-sm font-bold text-navy">{goal.label}</span>
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 text-[0.65rem] ${
                          selected
                            ? 'border-teal bg-teal text-white'
                            : 'border-slate-300 bg-white text-transparent'
                        }`}
                      >
                        ✓
                      </span>
                    </button>
                  )
                })}
              </div>
            </fieldset>

            <label className="block">
              <span className="mb-2 block text-sm font-extrabold text-navy">
                Additional Support <span className="font-semibold text-slate-text">(Optional)</span>
              </span>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-teal">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M12 20s-7-4.4-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.6-7 10-7 10z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
                <select
                  value={support}
                  onChange={(event) => setSupport(event.target.value)}
                  className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-3 pr-4 pl-11 text-sm font-semibold text-navy outline-none focus:border-teal focus:ring-2 focus:ring-teal/20"
                >
                  <option value="">Select all that apply</option>
                  {supportOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            </label>
          </form>
        </section>

        <InfoPanel
          className="hidden lg:block"
          illustration={<ProfileIllustration />}
          title="A more personal learning experience."
          items={[
            'Lessons that fit their level',
            'Practice focused on their goals',
            'Support for different learning needs',
          ]}
        />
      </div>

      <OnboardingFooter
        currentStep="profile"
        backTo="/get-started"
        continueTo="/onboarding/device-setup"
      />
    </OnboardingShell>
  )
}
