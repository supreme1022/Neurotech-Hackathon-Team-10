import { Logo } from '../ui/Logo'

const links = [
  { label: 'Product', href: '#product' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'For Educators', href: '#educators' },
  { label: 'About', href: '#about' },
]

export function Footer() {
  return (
    <footer id="about" className="border-t border-slate-100 bg-white px-6 pt-10 pb-8 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-center gap-8 md:flex-row md:items-start md:justify-between">
          <Logo />

          <nav className="flex flex-wrap items-center justify-center gap-6" aria-label="Footer">
            {links.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-bold text-navy transition-colors hover:text-teal"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="text-center md:text-right">
            <p className="text-xs font-semibold tracking-wide text-slate-text uppercase">
              Contact
            </p>
            <a
              href="mailto:support@phonifide.com"
              className="mt-1 block text-sm font-extrabold text-navy hover:text-teal"
            >
              support@phonifide.com
            </a>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-slate-100 pt-6 text-sm text-slate-text sm:flex-row">
          <p>© 2026 PhoniFide. All rights reserved.</p>
          <div className="flex items-center gap-5">
            <a href="#privacy" className="hover:text-navy">
              Privacy
            </a>
            <a href="#terms" className="hover:text-navy">
              Terms
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
