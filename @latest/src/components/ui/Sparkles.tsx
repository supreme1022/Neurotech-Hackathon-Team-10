type SparklesProps = {
  className?: string
  color?: string
}

export function Sparkles({ className = '', color = '#f5c518' }: SparklesProps) {
  return (
    <svg
      className={className}
      width="22"
      height="22"
      viewBox="0 0 22 22"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M11 2L11.6 7.2" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
      <path d="M16.5 5.5L13.2 8.8" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
      <path d="M19 11L13.8 11.4" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}
