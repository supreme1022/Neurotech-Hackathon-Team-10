import type { ReactNode } from 'react'
import { DashboardSidebar, type SidebarItem } from './DashboardSidebar'

type DashboardShellProps = {
  items: SidebarItem[]
  sectionLabel?: string
  sidebarFooter?: ReactNode
  topBar?: ReactNode
  children: ReactNode
  className?: string
}

export function DashboardShell({
  items,
  sectionLabel,
  sidebarFooter,
  topBar,
  children,
  className = '',
}: DashboardShellProps) {
  return (
    <main className="relative min-h-svh overflow-hidden bg-[#f7fafc]">
      <div
        className="pointer-events-none absolute -left-20 -top-16 h-64 w-64 rounded-full bg-[#d7f0ee]/70 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute bottom-0 left-0 h-56 w-[40%] rounded-[100%] bg-gradient-to-tr from-[#c5ebe9]/80 to-transparent blur-2xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute right-0 bottom-0 h-56 w-[40%] rounded-[100%] bg-gradient-to-tl from-[#ddd6fe]/70 to-transparent blur-2xl"
        aria-hidden="true"
      />

      <div className={`relative mx-auto flex min-h-svh max-w-[1400px] gap-5 p-4 lg:gap-6 lg:p-6 ${className}`}>
        <div className="hidden md:block">
          <DashboardSidebar items={items} sectionLabel={sectionLabel} footer={sidebarFooter} />
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          {topBar ? <div className="mb-5">{topBar}</div> : null}
          <div className="flex-1">{children}</div>
        </div>
      </div>
    </main>
  )
}
