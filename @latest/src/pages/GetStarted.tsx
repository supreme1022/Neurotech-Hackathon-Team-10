import { useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { RoleCard } from '../components/get-started/RoleCard'
import { Logo } from '../components/ui/Logo'
import { Sparkles } from '../components/ui/Sparkles'

type RoleId = 'student' | 'parent' | 'educator'

function StudentIcon() {
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" aria-hidden="true">
      <path
        d="M22 30c0-8 6.5-14.5 14-14.5S50 22 50 30v6c0 2.2-1.2 4.2-3.1 5.2L44 43v4.5c0 1.7-1.3 3-3 3H31c-1.7 0-3-1.3-3-3V43l-2.9-1.8C23.2 40.2 22 38.2 22 36v-6z"
        stroke="#0f9e98"
        strokeWidth="3"
        strokeLinejoin="round"
      />
      <path d="M22 32H17c-1.7 0-3 1.3-3 3v4c0 1.7 1.3 3 3 3h5" stroke="#0f9e98" strokeWidth="3" strokeLinecap="round" />
      <path d="M50 32h5c1.7 0 3 1.3 3 3v4c0 1.7-1.3 3-3 3h-5" stroke="#0f9e98" strokeWidth="3" strokeLinecap="round" />
      <circle cx="36" cy="30" r="5.5" stroke="#0f9e98" strokeWidth="2.5" />
      <circle cx="36" cy="30" r="2.2" fill="#0f9e98" />
      <path d="M54 18l3-4M58 22l5-1M52 14l1-5" stroke="#7c6cf0" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

function ParentIcon() {
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" aria-hidden="true">
      <circle cx="28" cy="24" r="9" fill="#0f9e98" />
      <path d="M12 54c1.5-10 8-15 16-15s14.5 5 16 15" fill="#0f9e98" />
      <circle cx="48" cy="28" r="7" fill="#5eead4" />
      <path d="M36 54c1-7 5.5-11 12-11s11 4 12 11" fill="#5eead4" />
      <path d="M56 16l2.5-4M60 19l4-.5M55 12l.5-4" stroke="#f5c518" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

function EducatorIcon() {
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" aria-hidden="true">
      <rect x="16" y="18" width="28" height="38" rx="4" stroke="#0f9e98" strokeWidth="3" />
      <rect x="24" y="14" width="12" height="7" rx="2" fill="#0f9e98" />
      <path d="M23 32h14M23 39h14M23 46h9" stroke="#0f9e98" strokeWidth="2.5" strokeLinecap="round" />
      <rect x="48" y="42" width="6" height="12" rx="1.5" fill="#a3e635" />
      <rect x="56" y="34" width="6" height="20" rx="1.5" fill="#8bc53f" />
      <rect x="64" y="26" width="6" height="28" rx="1.5" fill="#65a30d" />
      <path d="M58 14l2-3.5M62 16l3.5-.5M57 10l.4-3.5" stroke="#7c6cf0" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

const roles: Array<{
  id: RoleId
  title: string
  description: string
  icon: ReactNode
  footerLink?: { label: string }
}> = [
  {
    id: 'student',
    title: "I'm a Student",
    description: 'Learn, practice, and grow.',
    icon: <StudentIcon />,
    footerLink: { label: 'Enter student code' },
  },
  {
    id: 'parent',
    title: "I'm a Parent",
    description: "Support your child's learning.",
    icon: <ParentIcon />,
  },
  {
    id: 'educator',
    title: "I'm an Educator",
    description: 'Create lessons and track progress.',
    icon: <EducatorIcon />,
  },
]

export function GetStarted() {
  const navigate = useNavigate()
  const [selectedRole, setSelectedRole] = useState<RoleId>('student')

  function continueWithRole(role: RoleId) {
    setSelectedRole(role)
    navigate('/onboarding/learning-profile')
  }

  return (
    <main className="relative min-h-svh overflow-hidden bg-white">
      <div
        className="pointer-events-none absolute -left-20 -top-16 h-64 w-64 rounded-full bg-[#d9f1f3]/80 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute bottom-0 left-0 h-56 w-[45%] rounded-[100%] bg-gradient-to-tr from-[#c5ebe9] to-transparent blur-2xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute bottom-0 right-0 h-56 w-[45%] rounded-[100%] bg-gradient-to-tl from-[#ddd6fe]/80 to-transparent blur-2xl"
        aria-hidden="true"
      />

      <div className="relative mx-auto flex min-h-svh w-full max-w-6xl flex-col px-6 py-5 lg:px-8">
        <header className="flex items-center justify-between">
          <Logo />
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-bold text-navy transition-colors hover:text-teal"
          >
            <span className="text-teal" aria-hidden="true">
              ←
            </span>
            Back to Home
          </Link>
        </header>

        <div className="flex flex-1 flex-col items-center justify-center py-10 sm:py-12">
          <div className="relative text-center">
            <h1 className="text-3xl font-extrabold tracking-tight text-navy sm:text-4xl lg:text-[2.6rem]">
              How will you use{' '}
              <span className="relative inline-block">
                PhoniFide?
                <span className="absolute -right-5 -top-3 sm:-right-6 sm:-top-4">
                  <Sparkles />
                </span>
              </span>
            </h1>
            <p className="mt-3 text-base text-slate-text sm:text-lg">
              Choose your experience to get started.
            </p>
          </div>

          <div className="mt-10 grid w-full max-w-5xl gap-5 sm:grid-cols-2 lg:mt-12 lg:grid-cols-3 lg:gap-6">
            {roles.map((role) => (
              <RoleCard
                key={role.id}
                title={role.title}
                description={role.description}
                icon={role.icon}
                selected={selectedRole === role.id}
                onSelect={() => setSelectedRole(role.id)}
                onContinue={() => continueWithRole(role.id)}
                footerLink={role.footerLink}
              />
            ))}
          </div>

          <div className="relative mt-12 w-full max-w-xl">
            <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-slate-200" />
            <p className="relative mx-auto w-fit bg-white px-4 text-sm text-slate-text sm:text-[0.95rem]">
              Already have an account?{' '}
              <a href="#login" className="font-bold text-teal underline underline-offset-2 hover:text-teal-dark">
                Log in
              </a>
            </p>
          </div>

          <p className="mt-8 flex items-center gap-2 text-center text-sm text-slate-text">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="5" y="11" width="14" height="10" rx="2" stroke="#0f9e98" strokeWidth="2" />
              <path d="M8 11V8a4 4 0 118 0v3" stroke="#0f9e98" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Student profiles are managed securely by parents and educators.
          </p>
        </div>

        <div className="flex justify-end pb-2 text-sm text-slate-text">
          <a href="#privacy" className="hover:text-navy">
            Privacy
          </a>
          <span className="mx-2 text-slate-300" aria-hidden="true">
            |
          </span>
          <a href="#help" className="hover:text-navy">
            Help
          </a>
        </div>
      </div>
    </main>
  )
}
