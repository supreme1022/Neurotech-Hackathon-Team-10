import { Button } from '../ui/Button'

export function CTABanner() {
  return (
    <section className="bg-white px-6 pb-16 lg:px-8 lg:pb-20">
      <div className="relative mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#14b8a6] via-teal to-[#0b7f7a] px-6 py-14 text-center sm:px-10 lg:rounded-[2.5rem] lg:py-16">
        <div
          className="pointer-events-none absolute -left-10 top-0 h-40 w-64 rounded-full bg-white/10 blur-2xl"
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute -right-8 bottom-0 h-48 w-72 rounded-full bg-teal-dark/40 blur-2xl"
          aria-hidden="true"
        />
        <svg
          className="pointer-events-none absolute inset-0 h-full w-full opacity-30"
          viewBox="0 0 800 280"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path
            d="M0 180C120 120 220 220 340 160C460 100 560 200 700 140C760 120 800 150 800 150V280H0V180Z"
            fill="white"
            opacity="0.12"
          />
          <path
            d="M0 80C100 140 200 40 320 90C440 140 540 50 680 100C740 120 800 70 800 70V0H0V80Z"
            fill="white"
            opacity="0.08"
          />
        </svg>

        <div className="relative mx-auto max-w-2xl">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Make reading more accessible.
          </h2>
          <p className="mt-4 text-base text-white/90 sm:text-lg">
            Give every student a simple, effective way to build phonics skills.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button to="/get-started" variant="white" className="px-7 py-3">
              Get Started
              <span aria-hidden="true">→</span>
            </Button>
            <Button to="/get-started" variant="outlineLight" className="px-7 py-3">
              For Educators
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
