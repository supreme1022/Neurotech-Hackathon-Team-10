import type { ReactNode } from 'react'
import { Button } from '../ui/Button'

type RoleCardProps = {
  title: string
  description: string
  icon: ReactNode
  selected?: boolean
  onSelect?: () => void
  onContinue?: () => void
  footerLink?: {
    label: string
    href?: string
    onClick?: () => void
  }
}

export function RoleCard({
  title,
  description,
  icon,
  selected = false,
  onSelect,
  onContinue,
  footerLink,
}: RoleCardProps) {
  return (
    <article
      onClick={onSelect}
      className={`flex h-full cursor-pointer flex-col items-center rounded-[1.75rem] bg-white px-6 py-8 text-center shadow-[0_14px_40px_rgba(15,31,58,0.08)] transition-all duration-200 ${
        selected
          ? 'border-[2.5px] border-teal ring-4 ring-teal/10'
          : 'border-[2.5px] border-transparent hover:border-teal/40'
      }`}
    >
      <div className="mb-5 flex h-20 w-20 items-center justify-center">{icon}</div>

      <h2 className="text-xl font-extrabold tracking-tight text-navy">{title}</h2>
      <p className="mt-2 text-[0.95rem] leading-relaxed text-slate-text">{description}</p>

      <div className="mt-auto w-full pt-7">
        <Button
          variant="primary"
          className="w-full px-5 py-3"
          onClick={(event) => {
            event.stopPropagation()
            onSelect?.()
            onContinue?.()
          }}
        >
          Continue
          <span aria-hidden="true">→</span>
        </Button>

        {footerLink ? (
          <a
            href={footerLink.href ?? '#'}
            onClick={(event) => {
              event.stopPropagation()
              if (footerLink.onClick) {
                event.preventDefault()
                footerLink.onClick()
              }
            }}
            className="mt-4 inline-block text-sm font-bold text-teal underline underline-offset-2 hover:text-teal-dark"
          >
            {footerLink.label}
          </a>
        ) : (
          <span className="mt-4 inline-block h-5" aria-hidden="true" />
        )}
      </div>
    </article>
  )
}
