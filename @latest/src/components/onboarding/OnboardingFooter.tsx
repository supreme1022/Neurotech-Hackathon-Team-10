import { Button } from '../ui/Button'
import { ONBOARDING_STEPS, type OnboardingStepId } from './OnboardingStepper'

type OnboardingFooterProps = {
  currentStep: OnboardingStepId
  backTo: string
  continueTo?: string
  onContinue?: () => void
  continueLabel?: string
}

export function OnboardingFooter({
  currentStep,
  backTo,
  continueTo,
  onContinue,
  continueLabel = 'Continue',
}: OnboardingFooterProps) {
  const currentIndex = ONBOARDING_STEPS.findIndex((step) => step.id === currentStep)

  return (
    <div className="mt-8 flex items-center justify-between gap-4">
      <Button to={backTo} variant="ghost" className="border-teal text-teal hover:bg-teal-light px-6">
        <span aria-hidden="true">←</span>
        Back
      </Button>

      <div className="flex items-center gap-2" aria-label="Onboarding progress">
        {ONBOARDING_STEPS.map((step, index) => (
          <span
            key={step.id}
            className={`h-2.5 w-2.5 rounded-full ${
              index <= currentIndex ? 'bg-teal' : 'bg-slate-300'
            }`}
          />
        ))}
      </div>

      <Button
        to={continueTo}
        onClick={onContinue}
        variant="primary"
        className="px-7 py-3"
      >
        {continueLabel}
        <span aria-hidden="true">→</span>
      </Button>
    </div>
  )
}
