import { Clock, Mail, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function PendingValidation() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleBackToLogin = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Icon */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-amber-100 rounded-full mb-4">
            <Clock className="w-10 h-10 text-amber-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Compte en attente de validation</h1>
        </div>

        {/* Message Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="space-y-4 text-center">
            <p className="text-gray-600">
              Votre compte a bien été créé, mais il doit être validé par un administrateur avant que vous puissiez accéder au dashboard.
            </p>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800">
                <strong>Que faire ?</strong>
                <br />
                Contactez l'administrateur de votre département pour demander l'activation de votre compte.
              </p>
            </div>

            <div className="flex items-center justify-center gap-2 text-gray-500">
              <Mail className="w-4 h-4" />
              <span className="text-sm">Un email peut avoir été envoyé à l'administrateur</span>
            </div>
          </div>

          <div className="mt-8 space-y-3">
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Vérifier à nouveau
            </button>
            
            <button
              onClick={handleBackToLogin}
              className="w-full flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </button>
          </div>
        </div>

        {/* Help */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Besoin d'aide ?{' '}
            <a href="mailto:admin@iut.fr" className="text-blue-600 hover:underline">
              Contacter le support
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
