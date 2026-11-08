import {
  BookIcon,
  CalendarIcon,
  CapIcon,
  ChartIcon,
  ClipboardIcon,
  ClockIcon,
  HomeIcon,
  SettingsIcon,
  TrophyIcon,
  UsersIcon,
} from './icons'
import type { SidebarItem } from './DashboardSidebar'

export const studentNav: SidebarItem[] = [
  { label: 'Home', to: '/dashboard', icon: <HomeIcon /> },
  { label: 'Lessons', to: '/dashboard/lessons', icon: <BookIcon /> },
  { label: 'Progress', to: '/dashboard/lesson/results', icon: <ChartIcon /> },
  { label: 'Rewards', to: '/dashboard', icon: <TrophyIcon /> },
  { label: 'Settings', to: '/dashboard/settings', icon: <SettingsIcon /> },
]

export const studentHomeNav: SidebarItem[] = [
  { label: 'Home', to: '/dashboard', icon: <HomeIcon /> },
  { label: 'My Lessons', to: '/dashboard/lessons', icon: <BookIcon /> },
  { label: 'My Progress', to: '/dashboard/lesson/results', icon: <ClockIcon /> },
  { label: 'Learning Profile', to: '/onboarding/learning-profile', icon: <CapIcon /> },
  { label: 'Settings', to: '/dashboard/settings', icon: <SettingsIcon /> },
]

export const educatorNav: SidebarItem[] = [
  { label: 'Home', to: '/dashboard/educator', icon: <HomeIcon /> },
  { label: 'Students', to: '/dashboard/educator', icon: <UsersIcon /> },
  { label: 'Progress', to: '/dashboard/educator', icon: <ChartIcon /> },
  { label: 'Assignments', to: '/dashboard/educator', icon: <ClipboardIcon /> },
  { label: 'Sessions', to: '/dashboard/educator', icon: <CalendarIcon /> },
  { label: 'Reports', to: '/dashboard/educator', icon: <BookIcon /> },
  { label: 'Settings', to: '/dashboard/settings', icon: <SettingsIcon /> },
]
