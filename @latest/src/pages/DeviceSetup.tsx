import { useState } from 'react'
import { InfoPanel } from '../components/onboarding/InfoPanel'
import { OnboardingFooter } from '../components/onboarding/OnboardingFooter'
import { OnboardingShell } from '../components/onboarding/OnboardingShell'
import { OnboardingStepper } from '../components/onboarding/OnboardingStepper'
import { Button } from '../components/ui/Button'
import { Sparkles } from '../components/ui/Sparkles'

const calibrationSteps = [
  { id: 1, label: 'Look left' },
  { id: 2, label: 'Look right' },
  { id: 3, label: 'Hold steady' },
] as const

const holdTimeOptions = ['Short', 'Medium', 'Long'] as const

function DeviceIllustration() {
  return (
    <svg width="170" height="130" viewBox="0 0 170 130" fill="none" aria-hidden="true">
      <ellipse cx="88" cy="118" rx="48" ry="8" fill="#b6e7e3" />
      <circle cx="70" cy="48" r="22" fill="#fde68a" />
      <path d="M48 48c0-14 10-24 22-24s22 10 22 24" fill="#fbbf24" />
      <path d="M52 70c4 18 14 28 30 28s26-10 30-28" fill="#5eead4" />
      <path
        d="M48 42c0-8 6-14 14-14h16c8 0 14 6 14 14v6c0 2.5-1.5 4.5-3.8 5.4L84 52v5H68v-5l-4.2-2.6C61.5 52.5 60 50.5 60 48v-6z"
        stroke="#0f9e98"
        strokeWidth="3.5"
        fill="#ccfbf1"
      />
      <rect x="100" y="58" width="48" height="34" rx="4" fill="#0f9e98" />
      <rect x="104" y="62" width="40" height="22" rx="2" fill="#ecfeff" />
      <rect x="112" y="92" width="24" height="4" rx="2" fill="#0d9488" />
      <circle cx="124" cy="48" r="10" fill="#ddd6fe" stroke="#7c6cf0" strokeWidth="2" />
      <circle cx="124" cy="48" r="3.5" fill="#7c6cf0" />
      <path d="M148 30l3-5M154 34l6-1M146 24l1-5" stroke="#f5c518" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

export function DeviceSetup() {
  const [activeCalibration, setActiveCalibration] = useState(2)
  const [sensitivity, setSensitivity] = useState(55)
  const [holdTime, setHoldTime] = useState<(typeof holdTimeOptions)[number]>('Medium')
  const [audioPrompts, setAudioPrompts] = useState(true)

  return (
    <OnboardingShell showHomeIcon>
      <div className="mb-8 text-center">
        <h1 className="relative inline-block text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
          Let&apos;s get everything ready.
          <span className="absolute -right-6 -top-3">
            <Sparkles />
          </span>
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-base text-slate-text">
          Connect the headset and calibrate eye movement so PhoniFide can personalize the
          experience.
        </p>
      </div>

      <div className="grid flex-1 gap-6 lg:grid-cols-[240px_minmax(0,1fr)_240px] xl:grid-cols-[260px_minmax(0,1fr)_260px]">
        <OnboardingStepper currentStep="device" showIntro />

        <section className="space-y-4 rounded-[1.75rem] border border-slate-100 bg-white p-5 shadow-[0_16px_40px_rgba(15,31,58,0.06)] sm:p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-100 bg-[#f8fafc] p-4">
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-light">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M4 10v4a2 2 0 002 2h1l3 3V5L7 8H6a2 2 0 00-2 2z"
                      fill="#0f9e98"
                    />
                    <path
                      d="M15 9a3 3 0 010 6M17.5 7a5.5 5.5 0 010 10"
                      stroke="#0f9e98"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-extrabold text-navy">Headset Connection</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-xs font-semibold text-[#16a34a]">
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#22c55e] text-[0.55rem] text-white">
                      ✓
                    </span>
                    Device detected
                  </p>
                </div>
              </div>
              <Button variant="primary" className="w-full py-2 text-sm">
                Reconnect
              </Button>
            </div>

            <div className="rounded-2xl border border-slate-100 bg-[#f8fafc] p-4">
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-mint">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="13" width="4" height="7" rx="1" fill="#0f9e98" />
                    <rect x="10" y="9" width="4" height="11" rx="1" fill="#0f9e98" />
                    <rect x="16" y="5" width="4" height="15" rx="1" fill="#0f9e98" />
                  </svg>
                </div>
                <p className="text-sm font-extrabold text-navy">Signal Quality</p>
              </div>
              <div className="mb-3 grid grid-cols-3 gap-2">
                {['Left', 'Center', 'Right'].map((label) => (
                  <div key={label} className="text-center">
                    <div className="mx-auto mb-1 h-10 w-3 overflow-hidden rounded-full bg-slate-200">
                      <div className="mt-1 h-8 w-full rounded-full bg-[#22c55e]" />
                    </div>
                    <span className="text-[0.65rem] font-bold text-slate-text">{label}</span>
                  </div>
                ))}
              </div>
              <p className="flex items-center gap-1.5 text-xs font-semibold text-[#16a34a]">
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#22c55e] text-[0.55rem] text-white">
                  ✓
                </span>
                Ready for calibration
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-[#f8fafc] p-4 sm:p-5">
            <h2 className="mb-3 text-sm font-extrabold text-navy">Calibration Preview</h2>
            <div className="flex min-h-[170px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#c4b5fd] bg-[#f5f3ff] px-4 py-6">
              <svg width="220" height="70" viewBox="0 0 220 70" fill="none" aria-hidden="true">
                <circle cx="30" cy="35" r="16" fill="#5eead4" stroke="#0f9e98" strokeWidth="3" />
                <circle cx="110" cy="35" r="16" fill="#99f6e4" stroke="#0f9e98" strokeWidth="3" />
                <circle cx="190" cy="35" r="16" fill="#ccfbf1" stroke="#0f9e98" strokeWidth="3" />
                <path
                  d="M50 35C70 18 90 18 110 35"
                  stroke="#0f9e98"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                  fill="none"
                />
                <path
                  d="M130 35C150 52 170 52 190 35"
                  stroke="#0f9e98"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                  fill="none"
                />
                <text x="22" y="68" fill="#4a5568" fontSize="10" fontWeight="700">
                  Left
                </text>
                <text x="98" y="68" fill="#4a5568" fontSize="10" fontWeight="700">
                  Center
                </text>
                <text x="178" y="68" fill="#4a5568" fontSize="10" fontWeight="700">
                  Right
                </text>
              </svg>
              <p className="mt-4 max-w-sm text-center text-xs font-semibold text-slate-text">
                Placeholder for animated eye-movement calibration (future feature)
              </p>
            </div>

            <div className="mt-4 grid gap-2 sm:grid-cols-3">
              {calibrationSteps.map((step) => {
                const active = activeCalibration === step.id
                return (
                  <button
                    key={step.id}
                    type="button"
                    onClick={() => setActiveCalibration(step.id)}
                    className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-bold transition-colors ${
                      active
                        ? 'bg-teal text-white'
                        : 'border border-slate-200 bg-white text-navy hover:border-teal/40'
                    }`}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle cx="12" cy="12" r="7" stroke="currentColor" strokeWidth="2" />
                      <circle cx="12" cy="12" r="2.5" fill="currentColor" />
                    </svg>
                    {step.id}. {step.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-[#f8fafc] p-4 sm:p-5">
            <h2 className="mb-4 text-sm font-extrabold text-navy">Accessibility Settings</h2>

            <div className="space-y-5">
              <label className="block">
                <span className="mb-2 flex items-center gap-1.5 text-sm font-bold text-navy">
                  Sensitivity
                  <span
                    className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[0.6rem] text-slate-text"
                    title="How easily eye movements register as selections"
                  >
                    i
                  </span>
                </span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={sensitivity}
                  onChange={(event) => setSensitivity(Number(event.target.value))}
                  className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-teal"
                />
              </label>

              <fieldset>
                <legend className="mb-2 text-sm font-bold text-navy">Hold Time</legend>
                <div className="inline-flex rounded-full border border-slate-200 bg-white p-1">
                  {holdTimeOptions.map((option) => {
                    const selected = holdTime === option
                    return (
                      <button
                        key={option}
                        type="button"
                        onClick={() => setHoldTime(option)}
                        className={`rounded-full px-4 py-1.5 text-sm font-bold transition-colors ${
                          selected ? 'bg-teal text-white' : 'text-navy hover:bg-page'
                        }`}
                      >
                        {option}
                      </button>
                    )
                  })}
                </div>
              </fieldset>

              <div className="flex items-center justify-between gap-4">
                <span className="text-sm font-bold text-navy">Audio Prompts</span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={audioPrompts}
                  onClick={() => setAudioPrompts((value) => !value)}
                  className={`relative h-7 w-12 rounded-full transition-colors ${
                    audioPrompts ? 'bg-teal' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 h-6 w-6 rounded-full bg-white shadow transition-transform ${
                      audioPrompts ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>

            <p className="mt-5 text-xs text-slate-text">
              Your setup preferences can be changed later in Settings.
            </p>
          </div>
        </section>

        <InfoPanel
          className="hidden lg:block"
          illustration={<DeviceIllustration />}
          title="A smoother start to learning."
          items={[
            'Simple guided setup',
            'Adjusts to learner needs',
            'Ready for future lessons',
          ]}
        />
      </div>

      <OnboardingFooter
        currentStep="device"
        backTo="/onboarding/learning-profile"
        continueTo="/onboarding/ready"
      />
    </OnboardingShell>
  )
}
