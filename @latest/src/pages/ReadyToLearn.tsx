import { Link } from 'react-router-dom'
import { OnboardingFooter } from '../components/onboarding/OnboardingFooter'
import { OnboardingShell } from '../components/onboarding/OnboardingShell'
import { OnboardingStepper } from '../components/onboarding/OnboardingStepper'
import { Button } from '../components/ui/Button'
import { Sparkles } from '../components/ui/Sparkles'

export function ReadyToLearn() {
  return (
    <OnboardingShell>
      <div className="mb-8 text-center">
        <p className="text-xs font-extrabold tracking-[0.16em] text-teal uppercase">
          Ready to learn
        </p>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
          You&apos;re all set
          <span className="relative inline-block">
            .
            <span className="absolute -right-5 -top-4">
              <Sparkles />
            </span>
          </span>
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-base text-slate-text">
          Your learning profile and headset are ready. Start a hands-free phonics lesson when
          you&apos;re ready.
        </p>
      </div>

      <div className="grid flex-1 gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
        <OnboardingStepper currentStep="ready" showIntro />

        <section className="flex flex-col items-center justify-center rounded-[1.75rem] border border-slate-100 bg-white px-6 py-12 text-center shadow-[0_16px_40px_rgba(15,31,58,0.06)] sm:px-10">
          <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-teal-light text-3xl text-teal">
            ✓
          </div>
          <h2 className="text-2xl font-extrabold text-navy">Start your first lesson</h2>
          <p className="mt-3 max-w-md text-base leading-relaxed text-slate-text">
            Look left or right to choose answers while PhoniFide guides you with audio prompts and
            adapts to how you learn.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button to="/lesson" variant="primary" className="px-8 py-3">
              Begin Lesson
              <span aria-hidden="true">→</span>
            </Button>
            <Link
              to="/"
              className="text-sm font-bold text-teal underline underline-offset-2 hover:text-teal-dark"
            >
              Return to Home
            </Link>
          </div>
        </section>
      </div>

      <OnboardingFooter
        currentStep="ready"
        backTo="/onboarding/device-setup"
        continueTo="/lesson"
        continueLabel="Begin Lesson"
      />
    </OnboardingShell>
  )
}
