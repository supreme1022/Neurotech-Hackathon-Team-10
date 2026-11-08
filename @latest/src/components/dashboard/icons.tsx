type IconProps = { className?: string }

export function HomeIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 11.5L12 4l8 7.5V20a1 1 0 01-1 1h-5v-6H10v6H5a1 1 0 01-1-1v-8.5z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  )
}

export function BookIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 5h6v14H7a2 2 0 01-2-2V5zM13 5h6v12a2 2 0 01-2 2h-4V5z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  )
}

export function ChartIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 19V5M4 19h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <rect x="7" y="11" width="3" height="5" rx="0.5" fill="currentColor" />
      <rect x="12" y="8" width="3" height="8" rx="0.5" fill="currentColor" />
      <rect x="17" y="5" width="3" height="11" rx="0.5" fill="currentColor" />
    </svg>
  )
}

export function TrophyIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M8 5h8v4a4 4 0 01-8 0V5z" stroke="currentColor" strokeWidth="2" />
      <path d="M8 6H5a2 2 0 000 4h3M16 6h3a2 2 0 010 4h-3" stroke="currentColor" strokeWidth="2" />
      <path d="M12 13v3M9 20h6M10 16h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function SettingsIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function UsersIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="2" />
      <circle cx="17" cy="9" r="2.5" stroke="currentColor" strokeWidth="2" />
      <path d="M3.5 19c.5-3 2.8-4.5 5.5-4.5S14 16 14.5 19M14 15.5c1.2-.7 2.6-1 4-1 2 0 3.5 1 4 3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function ClipboardIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="5" y="5" width="14" height="16" rx="2" stroke="currentColor" strokeWidth="2" />
      <path d="M9 3.5h6V6H9V3.5zM8 11h8M8 15h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function CalendarIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="4" y="5" width="16" height="15" rx="2" stroke="currentColor" strokeWidth="2" />
      <path d="M8 3.5v3M16 3.5v3M4 9.5h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function CapIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M3 10l9-5 9 5-9 5-9-5z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M7 12v4c2 2 8 2 10 0v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function ClockIcon({ className = '' }: IconProps) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="2" />
      <path d="M12 8v5l3 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}
