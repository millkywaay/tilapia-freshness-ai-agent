import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Detect from './pages/Detect'

function App() {
  return (
    <div className="min-h-screen bg-[#050912] text-white relative">
      {/* Floating atmospheric orbs — fixed to viewport, clipped */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="orb orb-c" />
      </div>

      <div className="relative z-10">
        <Navbar />
        <Routes>
          <Route path="/"       element={<Landing />} />
          <Route path="/detect" element={<Detect />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
