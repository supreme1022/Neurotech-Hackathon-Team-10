import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from '../ui/Logo'

type OnboardingShellProps = {
  children: ReactNode
  homeLabel?: string
  showHomeIcon?: boolean
}

export function OnboardingShell({
  children,
  homeLabel = 'Back to Home',
  showHomeIcon = false,
}: OnboardingShellProps) {
  return (
    <main className="relative min-h-svh overflow-hidden bg-white">
      <div
        className="pointer-events-none absolute -left-24 -top-20 h-72 w-72 rounded-full bg-[#d7f0ee]/80 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute bottom-0 left-0 h-64 w-[42%] rounded-[100%] bg-gradient-to-tr from-[#c5ebe9] to-transparent blur-2xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute right-0 bottom-0 h-64 w-[42%] rounded-[100%] bg-gradient-to-tl from-[#ddd6fe]/80 to-transparent blur-2xl"
        aria-hidden="true"
      />

      <div className="relative mx-auto flex min-h-svh w-full max-w-7xl flex-col px-6 py-5 lg:px-8">
        <header className="flex items-center justify-between">
          <Logo />
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-bold text-navy transition-colors hover:text-teal"
          >
            {showHomeIcon ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M4 11.5L12 4l8 7.5V20a1 1 0 01-1 1h-5v-6H10v6H5a1 1 0 01-1-1v-8.5z"
                  stroke="#0f9e98"
                  strokeWidth="2"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <span className="text-teal" aria-hidden="true">
                ←
              </span>
            )}
            {homeLabel}
          </Link>
        </header>

        <div className="flex flex-1 flex-col py-8 lg:py-10">{children}</div>
      </div>
    </main>
  )
}
