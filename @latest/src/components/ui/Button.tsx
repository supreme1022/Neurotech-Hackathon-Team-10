import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Variant = 'primary' | 'secondary' | 'ghost' | 'white' | 'outlineLight'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  children: ReactNode
  to?: string
}

const variants: Record<Variant, string> = {
  primary:
    'bg-teal text-white hover:bg-teal-dark shadow-sm shadow-teal/20',
  secondary:
    'bg-white text-navy border-2 border-navy/80 hover:bg-page',
  ghost:
    'bg-transparent text-navy border-2 border-navy/70 hover:bg-white/70',
  white:
    'bg-white text-navy hover:bg-white/90 shadow-sm',
  outlineLight:
    'bg-transparent text-white border-2 border-white hover:bg-white/10',
}

const baseClass =
  'inline-flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-[0.95rem] font-bold transition-colors duration-200'

export function Button({
  variant = 'primary',
  className = '',
  children,
  to,
  ...props
}: ButtonProps) {
  const classes = `${baseClass} ${variants[variant]} ${className}`

  if (to) {
    return (
      <Link to={to} className={classes}>
        {children}
      </Link>
    )
  }

  return (
    <button type="button" className={classes} {...props}>
      {children}
    </button>
  )
}
