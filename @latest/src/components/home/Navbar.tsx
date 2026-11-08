import { Button } from '../ui/Button'
import { Logo } from '../ui/Logo'

const links = [
  { label: 'Product', href: '#product' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'For Educators', href: '#educators' },
  { label: 'About', href: '#about' },
]

export function Navbar() {
  return (
    <header className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5 lg:px-8">
      <Logo />

      <nav className="hidden items-center gap-8 md:flex" aria-label="Primary">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href}
            className="text-[0.95rem] font-semibold text-navy transition-colors hover:text-teal"
          >
            {link.label}
          </a>
        ))}
      </nav>

      <div className="flex items-center gap-3">
        <Button variant="ghost" className="hidden px-5 py-2 sm:inline-flex">
          Log In
        </Button>
        <Button to="/get-started" variant="primary" className="px-5 py-2">
          Get Started
        </Button>
      </div>
    </header>
  )
}
