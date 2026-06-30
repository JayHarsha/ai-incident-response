import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import IncidentPage from './pages/IncidentPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/incidents/:incidentId" element={<IncidentPage />} />
      </Routes>
    </BrowserRouter>
  )
}
