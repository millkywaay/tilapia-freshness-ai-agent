import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Detect from './pages/Detect'

function App() {
  return (
    <div className="app-shell min-h-screen">
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/detect" element={<Detect />} />
      </Routes>
    </div>
  )
}

export default App
