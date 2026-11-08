import type { ReactNode } from 'react'

type InfoPanelProps = {
  illustration: ReactNode
  title: string
  items: string[]
  className?: string
}

export function InfoPanel({ illustration, title, items, className = '' }: InfoPanelProps) {
  return (
    <aside className={`rounded-[1.5rem] bg-teal-light p-6 ${className}`}>
      <div className="mb-5 flex justify-center">{illustration}</div>
      <h3 className="text-lg font-extrabold leading-snug text-navy">{title}</h3>
      <ul className="mt-4 space-y-3">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2.5 text-sm font-semibold text-navy">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-teal text-[0.65rem] text-white">
              ✓
            </span>
            {item}
          </li>
        ))}
      </ul>
    </aside>
  )
}
