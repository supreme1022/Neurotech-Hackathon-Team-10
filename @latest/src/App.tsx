import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { DeviceSetup } from './pages/DeviceSetup'
import { GetStarted } from './pages/GetStarted'
import { Home } from './pages/Home'
import { LearningProfile } from './pages/LearningProfile'
import { Lesson } from './pages/Lesson'
import { ReadyToLearn } from './pages/ReadyToLearn'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/get-started" element={<GetStarted />} />
        <Route path="/onboarding/learning-profile" element={<LearningProfile />} />
        <Route path="/onboarding/device-setup" element={<DeviceSetup />} />
        <Route path="/onboarding/ready" element={<ReadyToLearn />} />
        <Route path="/lesson" element={<Lesson />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
