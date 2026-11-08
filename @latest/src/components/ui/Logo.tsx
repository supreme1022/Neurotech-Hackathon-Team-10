import { Link } from 'react-router-dom'

type LogoProps = {
  className?: string
  wordmarkClassName?: string
}

export function Logo({ className = '', wordmarkClassName = '' }: LogoProps) {
  return (
    <Link to="/" className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width="28"
        height="28"
        viewBox="0 0 28 28"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <rect x="3" y="14" width="3.5" height="10" rx="1.75" fill="#14b8a6" />
        <rect x="9" y="8" width="3.5" height="16" rx="1.75" fill="#0d9488" />
        <rect x="15" y="4" width="3.5" height="20" rx="1.75" fill="#6366f1" />
        <rect x="21" y="10" width="3.5" height="14" rx="1.75" fill="#a3e635" />
      </svg>
      <span className={`relative text-[1.35rem] font-extrabold tracking-tight text-navy ${wordmarkClassName}`}>
        PhoniFide
        <span className="pointer-events-none absolute -right-1 -top-2" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 1.5L7.4 5.2L10.5 3.2L8.2 6.1L11.5 7L8.2 7.9L10.5 10.8L7.4 8.8L7 12.5L6.6 8.8L3.5 10.8L5.8 7.9L2.5 7L5.8 6.1L3.5 3.2L6.6 5.2L7 1.5Z" fill="#f5c518" />
          </svg>
        </span>
      </span>
    </Link>
  )
}
