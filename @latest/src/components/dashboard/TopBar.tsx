import type { ReactNode } from 'react'

type TopBarProps = {
  title?: string
  breadcrumb?: string
  timer?: string
  showExit?: boolean
  onExit?: () => void
  rightSlot?: ReactNode
  userName?: string
  userInitial?: string
  showDeviceReady?: boolean
}

export function TopBar({
  title,
  breadcrumb,
  timer,
  showExit = false,
  onExit,
  rightSlot,
  userName = 'Jordan',
  userInitial = 'J',
  showDeviceReady = false,
}: TopBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="min-w-0">
        {title ? <h1 className="text-xl font-extrabold text-navy lg:text-2xl">{title}</h1> : null}
        {breadcrumb ? <p className="text-sm font-bold text-navy/80">{breadcrumb}</p> : null}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {showDeviceReady ? (
          <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-navy">
            <span className="text-teal" aria-hidden="true">
              ◐
            </span>
            Device ready
          </span>
        ) : null}

        {timer ? (
          <span className="inline-flex items-center gap-2 rounded-full bg-teal-light px-3 py-1.5 text-sm font-bold text-teal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="13" r="7" stroke="currentColor" strokeWidth="2" />
              <path d="M12 10v3l2 1M9 4h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            {timer}
          </span>
        ) : null}

        {rightSlot}

        <button
          type="button"
          className="relative rounded-full border border-slate-200 bg-white p-2 text-yellow"
          aria-label="Notifications"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6 9a6 6 0 1112 0c0 4 2 5 2 5H4s2-1 2-5zM10 19a2 2 0 004 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {showExit ? (
          <button
            type="button"
            onClick={onExit}
            className="inline-flex items-center gap-2 rounded-full border border-navy/70 bg-white px-4 py-2 text-sm font-bold text-navy hover:bg-page"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M10 7V5a2 2 0 012-2h7v18h-7a2 2 0 01-2-2v-2M3 12h11M7 8l-4 4 4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Exit Lesson
          </button>
        ) : (
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white py-1.5 pr-3 pl-1.5 text-sm font-bold text-navy"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-teal text-xs text-white">
              {userInitial}
            </span>
            {userName}
            <span aria-hidden="true">▾</span>
          </button>
        )}
      </div>
    </div>
  )
}
