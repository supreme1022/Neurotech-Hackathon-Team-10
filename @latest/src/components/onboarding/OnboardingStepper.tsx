export const ONBOARDING_STEPS = [
  { id: 'account', label: 'Create Account' },
  { id: 'profile', label: 'Learning Profile' },
  { id: 'device', label: 'Device Setup' },
  { id: 'ready', label: 'Ready to Learn' },
] as const

export type OnboardingStepId = (typeof ONBOARDING_STEPS)[number]['id']

type OnboardingStepperProps = {
  currentStep: OnboardingStepId
  showIntro?: boolean
}

export function OnboardingStepper({
  currentStep,
  showIntro = false,
}: OnboardingStepperProps) {
  const currentIndex = ONBOARDING_STEPS.findIndex((step) => step.id === currentStep)

  return (
    <aside className="rounded-[1.5rem] bg-[#f3f6f8] p-5 lg:p-6">
      {showIntro ? (
        <div className="mb-6">
          <h2 className="flex items-start gap-2 text-lg font-extrabold leading-snug text-navy">
            Get Started with PhoniFide
            <span className="mt-1 text-yellow" aria-hidden="true">
              ✦
            </span>
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-text">
            Set up your account and learning experience in just a few steps.
          </p>
        </div>
      ) : null}

      <ol className="space-y-3">
        {ONBOARDING_STEPS.map((step, index) => {
          const isComplete = index < currentIndex
          const isActive = index === currentIndex

          return (
            <li key={step.id}>
              <div
                className={`flex items-center gap-3 rounded-full px-3 py-2.5 ${
                  isActive ? 'bg-teal-light' : ''
                }`}
              >
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-extrabold ${
                    isComplete
                      ? 'bg-[#22c55e] text-white'
                      : isActive
                        ? 'bg-teal text-white'
                        : 'border-2 border-slate-300 bg-white text-slate-text'
                  }`}
                >
                  {isComplete ? '✓' : index + 1}
                </span>
                <span
                  className={`text-sm font-bold ${
                    isActive ? 'text-navy' : isComplete ? 'text-navy/80' : 'text-slate-text'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            </li>
          )
        })}
      </ol>
    </aside>
  )
}
