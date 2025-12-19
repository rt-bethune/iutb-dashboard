import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  GraduationCap, 
  Users, 
  Wallet, 
  Calendar,
  Settings,
  Menu,
  Upload,
  Database,
  UserPlus,
  Building2,
  LogOut,
  User,
  Shield,
  AlertTriangle,
  BarChart3,
  RefreshCw,
  Target
} from 'lucide-react'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useDepartment, DEPARTMENTS, DEPARTMENT_NAMES, type Department } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'

// Define nav items with optional permission requirements
const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, permission: null },
  { 
    path: '/scolarite', 
    label: 'Scolarité', 
    icon: GraduationCap, 
    permission: 'can_view_scolarite' as const,
    children: [
      { path: '/alertes', label: 'Alertes', icon: AlertTriangle, permission: 'can_view_scolarite' as const },
      { path: '/indicateurs', label: 'Indicateurs', icon: BarChart3, permission: 'can_view_scolarite' as const },
      { path: '/analyse-modules', label: 'Analyse modules', icon: Target, permission: 'can_view_scolarite' as const },
    ]
  },
  { path: '/recrutement', label: 'Recrutement', icon: Users, permission: 'can_view_recrutement' as const },
  { path: '/budget', label: 'Budget', icon: Wallet, permission: 'can_view_budget' as const },
  { path: '/edt', label: 'EDT', icon: Calendar, permission: 'can_view_edt' as const },
]

const adminItems = [
  { path: '/admin', label: 'Administration', icon: Settings },
  { path: '/upload', label: 'Import', icon: Upload },
  { path: '/admin/budget', label: 'Gérer Budget', icon: Database },
  { path: '/admin/recrutement', label: 'Gérer Parcoursup', icon: UserPlus },
  { path: '/admin/users', label: 'Utilisateurs', icon: Shield },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const location = useLocation()
  const { department, setDepartment, departmentName } = useDepartment()
  const { user, logout, isAdmin, checkPermission } = useAuth()
  const queryClient = useQueryClient()

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Invalidate all queries to force refetch
    await queryClient.invalidateQueries()
    // Small delay for visual feedback
    setTimeout(() => setIsRefreshing(false), 500)
  }

  // Filter departments based on user permissions (show only departments where user has at least one permission)
  const accessibleDepartments = user?.is_superadmin 
    ? DEPARTMENTS 
    : DEPARTMENTS.filter(dept => user?.permissions[dept] !== undefined)

  // Filter nav items based on user permissions for current department (parent + children)
  const visibleNavItems = navItems
    .map(item => {
      const children = item.children?.filter(child => {
        if (!child.permission) return true
        return checkPermission(department, child.permission)
      }) ?? []
      return { ...item, children }
    })
    .filter(item => {
      if (item.permission && !checkPermission(department, item.permission)) {
        return false
      }
      // Keep item if it has no children or if at least one child is visible
      if (item.children && item.children.length === 0) {
        return !item.children.length
      }
      return true
    })

  const isPathActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(`${path}/`)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200
        transform transition-transform duration-200 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-gray-900">
            📊 Dept Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">Tableau de bord</p>
        </div>

        {/* Department Selector */}
        <div className="px-4 py-3 border-b border-gray-100">
          <label className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            <Building2 className="w-4 h-4" />
            Département
          </label>
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value as Department)}
            className="w-full px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {accessibleDepartments.map((dept) => (
              <option key={dept} value={dept}>
                {dept} - {DEPARTMENT_NAMES[dept]}
              </option>
            ))}
          </select>
        </div>

        <nav className="p-4 space-y-1">
          {visibleNavItems.map((item) => {
            const hasChildren = item.children && item.children.length > 0
            const isSectionActive = isPathActive(item.path) || item.children?.some(child => isPathActive(child.path))

            return (
              <div key={item.path} className="space-y-1">
                <NavLink
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                    ${isActive || isSectionActive
                      ? 'bg-primary-50 text-primary-700 font-medium' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
                  `}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </NavLink>

                {hasChildren && (
                  <div className="ml-3 space-y-1">
                    {item.children!.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path}
                        onClick={() => setSidebarOpen(false)}
                        className={({ isActive }) => `
                          flex items-center gap-3 px-7 py-2 rounded-lg text-sm transition-colors
                          ${isActive 
                            ? 'bg-primary-50 text-primary-700 font-medium' 
                            : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}
                        `}
                      >
                        <child.icon className="w-4 h-4" />
                        {child.label}
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            )
          })}

          {/* Separator */}
          <div className="my-4 border-t border-gray-200" />

          {/* Admin section - only show if user is admin */}
          {isAdmin() && (
            <>
              <p className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Administration
              </p>
              {adminItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-primary-50 text-primary-700 font-medium' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
                  `}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
          {/* User info */}
          {user && (
            <div className="mb-3 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-900">{user.cas_login}</span>
                {user.is_superadmin && (
                  <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                    Admin
                  </span>
                )}
              </div>
              <button
                onClick={logout}
                className="mt-2 w-full flex items-center justify-center gap-2 text-sm text-gray-600 hover:text-red-600 py-1"
              >
                <LogOut className="w-4 h-4" />
                Déconnexion
              </button>
            </div>
          )}
          <div className="text-xs text-gray-400">
            v0.1.0 
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="sticky top-0 z-30 bg-white border-b border-gray-200">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <div className="flex items-center gap-4 ml-auto">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
                title="Rafraîchir les données"
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <span className="px-3 py-1 text-sm font-medium text-primary-700 bg-primary-50 rounded-full">
                {department} - {departmentName}
              </span>
              <span className="text-sm text-gray-500">
                {new Date().toLocaleDateString('fr-FR', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
