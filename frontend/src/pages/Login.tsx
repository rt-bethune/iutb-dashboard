import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { LogIn, User, Building2, Loader2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const { isAuthenticated, isPending, isLoading, login } = useAuth()
  const [devUsername, setDevUsername] = useState('')
  const [showDevLogin, setShowDevLogin] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  // Show pending message
  if (isPending) {
    return <Navigate to="/auth/pending" replace />
  }

  const handleCASLogin = () => {
    login()
  }

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!devUsername.trim()) return
    
    setIsSubmitting(true)
    await login(devUsername.trim())
    setIsSubmitting(false)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-xl mb-4">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard Département</h1>
          <p className="text-gray-600 mt-2">Connectez-vous pour accéder au tableau de bord</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* CAS Login Button */}
          <button
            onClick={handleCASLogin}
            className="w-full flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            <LogIn className="w-5 h-5" />
            Se connecter avec CAS
          </button>

          <p className="text-center text-sm text-gray-500 mt-4">
            Utilisez vos identifiants universitaires
          </p>

          {/* Separator */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <button
                onClick={() => setShowDevLogin(!showDevLogin)}
                className="px-2 bg-white text-gray-400 hover:text-gray-600"
              >
                {showDevLogin ? 'Masquer' : 'Mode développement'}
              </button>
            </div>
          </div>

          {/* Dev Login Form */}
          {showDevLogin && (
            <form onSubmit={handleDevLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom d'utilisateur (dev)
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={devUsername}
                    onChange={(e) => setDevUsername(e.target.value)}
                    placeholder="admin, teacher1, etc."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={isSubmitting}
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={isSubmitting || !devUsername.trim()}
                className="w-full flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <LogIn className="w-4 h-4" />
                )}
                Connexion dev
              </button>
              <p className="text-xs text-gray-500 text-center">
                Le premier utilisateur devient automatiquement superadmin
              </p>
            </form>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500 mt-6">
          En cas de problème, contactez l'administrateur du département
        </p>
      </div>
    </div>
  )
}
