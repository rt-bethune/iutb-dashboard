import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Scolarite from './pages/Scolarite'
import Recrutement from './pages/Recrutement'
import Budget from './pages/Budget'
import EDT from './pages/EDT'
import Admin from './pages/Admin'
import AdminBudget from './pages/AdminBudget'
import AdminRecrutement from './pages/AdminRecrutement'
import Upload from './pages/Upload'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="scolarite" element={<Scolarite />} />
        <Route path="recrutement" element={<Recrutement />} />
        <Route path="budget" element={<Budget />} />
        <Route path="edt" element={<EDT />} />
        <Route path="upload" element={<Upload />} />
        <Route path="admin" element={<Admin />} />
        <Route path="admin/budget" element={<AdminBudget />} />
        <Route path="admin/recrutement" element={<AdminRecrutement />} />
      </Route>
    </Routes>
  )
}

export default App
