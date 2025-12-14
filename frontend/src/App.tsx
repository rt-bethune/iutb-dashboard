import { Routes, Route, Navigate } from 'react-router-dom'
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
import Login from './pages/Login'
import PendingValidation from './pages/PendingValidation'
import UsersManagement from './pages/UsersManagement'
import { useAuth } from './contexts/AuthContext'
import { Loader2 } from 'lucide-react'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, isPending } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (isPending) {
    return <Navigate to="/auth/pending" replace />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/auth/pending" element={<PendingValidation />} />

      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        <Route path="scolarite" element={<Scolarite />} />
        <Route path="recrutement" element={<Recrutement />} />
        <Route path="budget" element={<Budget />} />
        <Route path="edt" element={<EDT />} />
        <Route path="upload" element={<Upload />} />
        <Route path="admin" element={<Admin />} />
        <Route path="admin/budget" element={<AdminBudget />} />
        <Route path="admin/recrutement" element={<AdminRecrutement />} />
        <Route path="admin/users" element={<UsersManagement />} />
      </Route>
    </Routes>
  )
}

export default App
