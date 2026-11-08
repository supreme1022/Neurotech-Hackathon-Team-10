import { NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'
import { Logo } from '../ui/Logo'

export type SidebarItem = {
  label: string
  to: string
  icon: ReactNode
}

type DashboardSidebarProps = {
  items: SidebarItem[]
  sectionLabel?: string
  footer?: ReactNode
}

export function DashboardSidebar({
  items,
  sectionLabel = 'Your Space',
  footer,
}: DashboardSidebarProps) {
  return (
    <aside className="flex h-full w-[220px] shrink-0 flex-col rounded-[1.75rem] border border-slate-100 bg-white p-4 shadow-[0_10px_30px_rgba(15,31,58,0.04)] lg:w-[240px]">
      <div className="mb-6 px-1">
        <Logo wordmarkClassName="text-[1.15rem]" />
      </div>

      <p className="mb-3 px-3 text-[0.7rem] font-extrabold tracking-[0.14em] text-slate-text uppercase">
        {sectionLabel}
      </p>

      <nav className="flex flex-1 flex-col gap-1" aria-label="Dashboard">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/dashboard' || item.to === '/dashboard/educator'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold transition-colors ${
                isActive
                  ? 'bg-teal-light text-teal'
                  : 'text-navy/80 hover:bg-page hover:text-navy'
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      {footer ? <div className="mt-4">{footer}</div> : null}
    </aside>
  )
}
