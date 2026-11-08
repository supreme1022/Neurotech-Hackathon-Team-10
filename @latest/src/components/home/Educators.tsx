const checklist = [
  'Monitor accuracy and progress',
  'Review missed sounds and words',
  'Personalize support for every learner',
]

function DashboardMockup() {
  const bars = [
    { label: 'Letter Sounds', width: '92%' },
    { label: 'Blending', width: '78%' },
    { label: 'Sight Words', width: '85%' },
  ]

  return (
    <div className="relative mx-auto w-full max-w-lg">
      <div
        className="absolute -left-6 top-8 h-56 w-56 rounded-full bg-teal-light blur-2xl sm:-left-10"
        aria-hidden="true"
      />

      <div className="relative rotate-[-4deg] overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-[0_24px_60px_rgba(15,31,58,0.14)]">
        <div className="flex min-h-[280px]">
          <aside className="flex w-[30%] flex-col gap-3 bg-navy px-3 py-5 sm:w-32 sm:px-4">
            <div className="mb-2 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-sm bg-teal" />
              <span className="truncate text-[0.65rem] font-bold text-white/90">PhoniFide</span>
            </div>
            {[
              { label: 'Home', active: true },
              { label: 'Lessons', active: false },
              { label: 'Progress', active: false },
              { label: 'Students', active: false },
            ].map((item) => (
              <div
                key={item.label}
                className={`rounded-lg px-2 py-1.5 text-[0.65rem] font-semibold sm:text-xs ${
                  item.active ? 'bg-teal text-white' : 'text-white/70'
                }`}
              >
                {item.label}
              </div>
            ))}
          </aside>

          <div className="flex-1 bg-[#f8fafc] p-4 sm:p-5">
            <h3 className="mb-4 text-sm font-extrabold text-navy sm:text-base">
              Student Progress
            </h3>
            <div className="space-y-4">
              {bars.map((bar) => (
                <div key={bar.label}>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="text-[0.7rem] font-semibold text-slate-text sm:text-xs">
                      {bar.label}
                    </span>
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-lime text-[0.55rem] text-white">
                      ✓
                    </span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-slate-200/80">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-teal to-[#34d399]"
                      style={{ width: bar.width }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function Educators() {
  return (
    <section id="educators" className="bg-white px-6 py-16 lg:px-8 lg:py-24">
      <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <DashboardMockup />

        <div className="text-left">
          <p className="text-xs font-extrabold tracking-[0.16em] text-teal uppercase">
            For Educators
          </p>
          <h2 className="mt-4 text-3xl font-extrabold leading-tight tracking-tight text-navy sm:text-4xl">
            See progress, support growth.
          </h2>
          <p className="mt-4 max-w-md text-base leading-relaxed text-slate-text sm:text-lg">
            Track learning, identify what&apos;s next, and support each student
            with confidence.
          </p>

          <ul className="mt-8 space-y-4">
            {checklist.map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal text-sm font-bold text-white">
                  ✓
                </span>
                <span className="font-semibold text-navy">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
