import { CTABanner } from '../components/home/CTABanner'
import { Educators } from '../components/home/Educators'
import { Footer } from '../components/home/Footer'
import { Hero } from '../components/home/Hero'
import { LearningGap } from '../components/home/LearningGap'

export function Home() {
  return (
    <main className="min-h-svh overflow-x-hidden bg-white">
      <Hero />
      <LearningGap />
      <Educators />
      <CTABanner />
      <Footer />
    </main>
  )
}
