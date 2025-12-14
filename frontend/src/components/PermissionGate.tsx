import { ReactNode } from 'react'
import { ShieldAlert, Lock } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useDepartment } from '@/contexts/DepartmentContext'

interface PermissionGateProps {
  children: ReactNode
  domain: 'scolarite' | 'recrutement' | 'budget' | 'edt'
  action?: 'view' | 'edit' | 'import' | 'export'
  department?: string
  fallback?: ReactNode
}

export default function PermissionGate({
  children,
  domain,
  action = 'view',
  department: propDepartment,
  fallback,
}: PermissionGateProps) {
  const { user, isAuthenticated, checkPermission } = useAuth()
  const { department: contextDepartment } = useDepartment()
  
  const department = propDepartment || contextDepartment

  // Not authenticated
  if (!isAuthenticated || !user) {
    return fallback || (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-500">
        <Lock className="w-16 h-16 mb-4 text-gray-300" />
        <h2 className="text-xl font-semibold mb-2">Authentification requise</h2>
        <p className="text-center max-w-md">
          Vous devez être connecté pour accéder à cette page.
        </p>
      </div>
    )
  }

  // Build permission key
  const permissionKey = action === 'import' || action === 'export'
    ? `can_${action}` as const
    : `can_${action}_${domain}` as const

  // Check permission
  const hasPermission = checkPermission(department, permissionKey as any)

  if (!hasPermission) {
    return fallback || (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-500">
        <ShieldAlert className="w-16 h-16 mb-4 text-orange-300" />
        <h2 className="text-xl font-semibold mb-2">Accès non autorisé</h2>
        <p className="text-center max-w-md">
          Vous n'avez pas la permission d'accéder aux données de{' '}
          <strong>{domain}</strong> pour le département <strong>{department}</strong>.
        </p>
        <p className="text-sm text-gray-400 mt-4">
          Contactez un administrateur pour obtenir les droits d'accès.
        </p>
      </div>
    )
  }

  return <>{children}</>
}

// Hook for checking permissions inline
export function useHasPermission(
  domain: 'scolarite' | 'recrutement' | 'budget' | 'edt',
  action: 'view' | 'edit' = 'view',
  department?: string
) {
  const { checkPermission, isAuthenticated } = useAuth()
  const { department: contextDepartment } = useDepartment()
  
  const dept = department || contextDepartment
  
  if (!isAuthenticated) return false
  
  const permissionKey = `can_${action}_${domain}` as const
  return checkPermission(dept, permissionKey as any)
}

// Component for conditional rendering based on permission
export function IfPermission({
  children,
  domain,
  action = 'view',
  department,
}: {
  children: ReactNode
  domain: 'scolarite' | 'recrutement' | 'budget' | 'edt'
  action?: 'view' | 'edit'
  department?: string
}) {
  const hasPermission = useHasPermission(domain, action, department)
  
  if (!hasPermission) return null
  return <>{children}</>
}
