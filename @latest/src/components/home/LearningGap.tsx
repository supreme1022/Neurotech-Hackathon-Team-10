import { Sparkles } from '../ui/Sparkles'

const stats = [
  {
    value: '1 in 5',
    description: 'students have a mental health or learning disability.',
    iconBg: 'text-teal',
    cardBg: 'bg-white',
    wave: 'teal',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="9" cy="8" r="3" fill="#0f9e98" />
        <circle cx="16" cy="9" r="2.5" fill="#0f9e98" opacity="0.85" />
        <path d="M3.5 19c.5-3 2.8-4.5 5.5-4.5S14 16 14.5 19" stroke="#0f9e98" strokeWidth="2" strokeLinecap="round" />
        <path d="M14 15.5c1.2-.7 2.6-1 4-1 2 0 3.5 1 4 3.5" stroke="#0f9e98" strokeWidth="2" strokeLinecap="round" opacity="0.85" />
      </svg>
    ),
  },
  {
    value: '500:1',
    description: 'average counselor-to-student ratio in public schools.',
    iconBg: 'text-teal',
    cardBg: 'bg-mint',
    wave: null,
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 3c-2.5 0-4.5 2.2-4.5 5.2 0 2.2 1 3.6 2 4.8-.2 1.4-1.2 2.4-2.5 3.2 1.8.4 3.4.2 4.5-.4 1.1.6 2.7.8 4.5.4-1.3-.8-2.3-1.8-2.5-3.2 1-1.2 2-2.6 2-4.8C16.5 5.2 14.5 3 12 3z"
          fill="#0f9e98"
        />
        <circle cx="10" cy="8.5" r="1" fill="white" />
        <circle cx="14" cy="8.5" r="1" fill="white" />
      </svg>
    ),
  },
  {
    value: '67%',
    description: 'of referrals go unactioned without structured follow-up.',
    iconBg: 'text-purple',
    cardBg: 'bg-white',
    wave: 'purple',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="4" y="5" width="16" height="15" rx="2.5" stroke="#7c6cf0" strokeWidth="2" />
        <path d="M8 3.5v3M16 3.5v3M4 9.5h16" stroke="#7c6cf0" strokeWidth="2" strokeLinecap="round" />
        <path d="M9 14.5l2 2 4-4" stroke="#7c6cf0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
]

const ribbonItems = [
  {
    label: 'Targeted Phonics Practice',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="4" y="14" width="16" height="4" rx="1.5" fill="#0f9e98" />
        <rect x="6" y="9" width="12" height="4" rx="1.5" fill="#0f9e98" opacity="0.75" />
        <rect x="8" y="4" width="8" height="4" rx="1.5" fill="#0f9e98" opacity="0.5" />
      </svg>
    ),
  },
  {
    label: 'Adjusts to Each Learner',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="4" y="13" width="4" height="7" rx="1" fill="#0f9e98" />
        <rect x="10" y="9" width="4" height="11" rx="1" fill="#0f9e98" />
        <rect x="16" y="5" width="4" height="15" rx="1" fill="#0f9e98" />
      </svg>
    ),
  },
  {
    label: 'Builds Reading Confidence',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 3.5l2.2 4.6 5 .7-3.6 3.5.9 5.1L12 15.2 7.5 17.4l.9-5.1L4.8 8.8l5-.7L12 3.5z"
          stroke="#f5c518"
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
]

export function LearningGap() {
  return (
    <section id="product" className="bg-page px-6 py-16 lg:px-8 lg:py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-extrabold tracking-[0.16em] text-teal uppercase">
            The Learning Gap
          </p>
          <h2 className="mt-4 text-3xl font-extrabold leading-tight tracking-tight text-navy sm:text-4xl lg:text-[2.6rem]">
            Too many students are still falling through the{' '}
            <span className="relative inline-block">
              cracks.
              <span className="absolute -right-5 -top-3">
                <Sparkles className="h-5 w-5" />
              </span>
            </span>
          </h2>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-3 md:gap-6">
          {stats.map((stat) => (
            <article
              key={stat.value}
              className={`relative overflow-hidden rounded-2xl p-6 shadow-[0_12px_30px_rgba(15,31,58,0.06)] ${stat.cardBg}`}
            >
              <div className="mb-5">{stat.icon}</div>
              <p className="text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
                {stat.value}
              </p>
              <p className="mt-3 text-[0.95rem] leading-relaxed text-slate-text">
                {stat.description}
              </p>

              {stat.wave === 'teal' && (
                <svg
                  className="absolute inset-x-0 bottom-0 h-10 w-full"
                  viewBox="0 0 320 40"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path
                    d="M0 24C40 10 80 34 120 22C160 10 200 30 240 18C280 6 300 20 320 14V40H0V24Z"
                    fill="#0f9e98"
                    opacity="0.18"
                  />
                </svg>
              )}
              {stat.wave === 'purple' && (
                <svg
                  className="absolute inset-x-0 bottom-0 h-10 w-full"
                  viewBox="0 0 320 40"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path
                    d="M0 20C50 32 90 8 140 20C190 32 230 10 280 22C300 28 310 18 320 16V40H0V20Z"
                    fill="#7c6cf0"
                    opacity="0.18"
                  />
                </svg>
              )}
            </article>
          ))}
        </div>

        <div className="mt-10 rounded-[2rem] bg-[#eef2f6] px-6 py-6 sm:px-8 lg:px-10">
          <div className="grid items-center gap-6 lg:grid-cols-[1.1fr_repeat(3,1fr)] lg:gap-0">
            <p className="text-center text-xl font-extrabold text-navy lg:pr-6 lg:text-left lg:text-[1.35rem]">
              Built for{' '}
              <span className="relative inline-block">
                early readers.
                <svg
                  className="absolute -bottom-1 left-0 w-full"
                  height="8"
                  viewBox="0 0 140 8"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path
                    d="M2 5C30 2 60 6 90 3C110 1 125 5 138 3"
                    stroke="#8bc53f"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    fill="none"
                  />
                </svg>
              </span>
            </p>

            {ribbonItems.map((item) => (
              <div
                key={item.label}
                className="flex flex-col items-center justify-center gap-2 text-center lg:border-l lg:border-slate-300/80 lg:px-4"
              >
                {item.icon}
                <span className="max-w-[9rem] text-sm font-extrabold leading-snug text-navy">
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
