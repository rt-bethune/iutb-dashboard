import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

interface User {
  id: number
  cas_login: string
  email: string | null
  nom: string | null
  prenom: string | null
  is_active: boolean
  is_superadmin: boolean
  permissions: Record<string, DepartmentPermissions>
}

interface DepartmentPermissions {
  can_view_scolarite: boolean
  can_edit_scolarite: boolean
  can_view_recrutement: boolean
  can_edit_recrutement: boolean
  can_view_budget: boolean
  can_edit_budget: boolean
  can_view_edt: boolean
  can_edit_edt: boolean
  can_import: boolean
  can_export: boolean
  is_dept_admin: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  isPending: boolean
  login: (username?: string) => void
  logout: () => void
  checkPermission: (department: string, permission: keyof DepartmentPermissions) => boolean
  isAdmin: (department?: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_URL = '/api'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'))
  const [isLoading, setIsLoading] = useState(true)
  const [isPending, setIsPending] = useState(false)

  // Check for token in URL (after CAS callback)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      localStorage.setItem('auth_token', urlToken)
      setToken(urlToken)
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  // Fetch user when token changes
  useEffect(() => {
    if (token) {
      fetchUser(token)
    } else {
      setUser(null)
      setIsLoading(false)
    }
  }, [token])

  const fetchUser = async (accessToken: string) => {
    setIsLoading(true)
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        params: { token: accessToken }
      })
      setUser(response.data)
      setIsPending(false)
    } catch (error: any) {
      if (error.response?.status === 403 && error.response?.data?.detail === 'Account not validated') {
        setIsPending(true)
      } else {
        // Invalid token
        localStorage.removeItem('auth_token')
        setToken(null)
      }
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username?: string) => {
    if (username) {
      // Dev login
      try {
        const response = await axios.post(`${API_URL}/auth/dev/login`, null, {
          params: { username }
        })
        
        if (response.data.pending) {
          setIsPending(true)
          return
        }
        
        const { token: newToken, user: userData } = response.data
        localStorage.setItem('auth_token', newToken)
        setToken(newToken)
        setUser(userData)
        setIsPending(false)
      } catch (error) {
        console.error('Dev login failed:', error)
      }
    } else {
      // CAS login - redirect to backend
      window.location.href = `${API_URL}/auth/login?return_url=${encodeURIComponent(window.location.origin)}`
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
    setIsPending(false)
    // Optionally redirect to CAS logout
    // window.location.href = `${API_URL}/auth/logout?return_url=${encodeURIComponent(window.location.origin)}`
  }

  const checkPermission = (department: string, permission: keyof DepartmentPermissions): boolean => {
    if (!user) return false
    if (user.is_superadmin) return true
    
    const deptPerms = user.permissions[department]
    if (!deptPerms) return false
    
    return deptPerms[permission]
  }

  const isAdmin = (department?: string): boolean => {
    if (!user) return false
    if (user.is_superadmin) return true
    
    if (department) {
      return user.permissions[department]?.is_dept_admin || false
    }
    
    // Check if admin of any department
    return Object.values(user.permissions).some(p => p.is_dept_admin)
  }

  return (
    <AuthContext.Provider value={{
      user,
      token,
      isLoading,
      isAuthenticated: !!user && !isPending,
      isPending,
      login,
      logout,
      checkPermission,
      isAdmin,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Permission check hook
export function usePermission(department: string, permission: keyof DepartmentPermissions) {
  const { checkPermission } = useAuth()
  return checkPermission(department, permission)
}

// Admin check hook
export function useIsAdmin(department?: string) {
  const { isAdmin } = useAuth()
  return isAdmin(department)
}
