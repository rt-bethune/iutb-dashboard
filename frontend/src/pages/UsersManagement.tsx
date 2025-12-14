import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Users, UserCheck, UserX, Shield, ShieldCheck, ChevronDown, ChevronRight,
  Check, X, Loader2, Search, Building2, Eye, Edit, Trash2, Save
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'

const API_URL = '/api'

interface User {
  id: number
  cas_login: string
  email: string | null
  nom: string | null
  prenom: string | null
  is_active: boolean
  is_superadmin: boolean
  date_creation: string | null
  date_derniere_connexion: string | null
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

const DEPARTMENTS = ['RT', 'GEII', 'GCCD', 'GMP', 'QLIO', 'CHIMIE']

const PERMISSION_LABELS: Record<keyof DepartmentPermissions, string> = {
  can_view_scolarite: 'Voir Scolarité',
  can_edit_scolarite: 'Modifier Scolarité',
  can_view_recrutement: 'Voir Recrutement',
  can_edit_recrutement: 'Modifier Recrutement',
  can_view_budget: 'Voir Budget',
  can_edit_budget: 'Modifier Budget',
  can_view_edt: 'Voir EDT',
  can_edit_edt: 'Modifier EDT',
  can_import: 'Importer',
  can_export: 'Exporter',
  is_dept_admin: 'Admin Département',
}

export default function UsersManagement() {
  const { token, user: currentUser, isAdmin } = useAuth()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<'all' | 'active' | 'pending'>('all')
  const [search, setSearch] = useState('')
  const [expandedUser, setExpandedUser] = useState<number | null>(null)
  const [editingPermissions, setEditingPermissions] = useState<{userId: number, dept: string} | null>(null)

  // Fetch users
  const { data: usersData, isLoading } = useQuery({
    queryKey: ['admin', 'users', filter, token],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/admin/users/users`, {
        params: { token, status: filter === 'all' ? undefined : filter }
      })
      return response.data
    },
    enabled: !!token,
  })

  // Fetch departments overview
  const { data: deptData } = useQuery({
    queryKey: ['admin', 'departments', token],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/admin/users/departments`, {
        params: { token }
      })
      return response.data
    },
    enabled: !!token,
  })

  // Validate user mutation
  const validateMutation = useMutation({
    mutationFn: async ({ userId, departments }: { userId: number; departments: string[] }) => {
      const response = await axios.post(
        `${API_URL}/admin/users/users/${userId}/validate`,
        null,
        { params: { token, departments } }
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  })

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: async ({ userId, data }: { userId: number; data: any }) => {
      const response = await axios.put(
        `${API_URL}/admin/users/users/${userId}`,
        data,
        { params: { token } }
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  })

  // Update permission mutation
  const updatePermissionMutation = useMutation({
    mutationFn: async ({ userId, department, permissions }: { userId: number; department: string; permissions: Partial<DepartmentPermissions> }) => {
      const response = await axios.put(
        `${API_URL}/admin/users/users/${userId}/permissions/${department}`,
        permissions,
        { params: { token } }
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      setEditingPermissions(null)
    },
  })

  // Delete user mutation
  const deleteMutation = useMutation({
    mutationFn: async (userId: number) => {
      await axios.delete(`${API_URL}/admin/users/users/${userId}`, {
        params: { token }
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  })

  const users: User[] = usersData?.users || []
  const filteredUsers = users.filter(u => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      u.cas_login.toLowerCase().includes(searchLower) ||
      u.email?.toLowerCase().includes(searchLower) ||
      u.nom?.toLowerCase().includes(searchLower) ||
      u.prenom?.toLowerCase().includes(searchLower)
    )
  })

  const pendingCount = deptData?.pending_users || 0

  if (!isAdmin()) {
    return (
      <div className="p-8 text-center">
        <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-700">Accès refusé</h2>
        <p className="text-gray-500 mt-2">Vous devez être administrateur pour accéder à cette page.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestion des utilisateurs</h1>
          <p className="text-gray-500 mt-1">Gérer les comptes et les permissions par département</p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 bg-amber-100 text-amber-800 px-4 py-2 rounded-lg">
            <UserX className="w-5 h-5" />
            <span className="font-medium">{pendingCount} compte(s) en attente</span>
          </div>
        )}
      </div>

      {/* Department Overview */}
      {deptData && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {deptData.departments.map((dept: any) => (
            <div key={dept.department} className="bg-white rounded-lg border p-4">
              <div className="flex items-center gap-2 mb-2">
                <Building2 className="w-5 h-5 text-blue-600" />
                <span className="font-semibold">{dept.department}</span>
              </div>
              <div className="text-sm text-gray-600">
                <div>{dept.user_count} utilisateur(s)</div>
                <div className="text-green-600">{dept.admin_count} admin(s)</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Tous
          </button>
          <button
            onClick={() => setFilter('active')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'active' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <UserCheck className="w-4 h-4 inline mr-1" />
            Actifs
          </button>
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'pending' ? 'bg-amber-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <UserX className="w-4 h-4 inline mr-1" />
            En attente
          </button>
        </div>
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un utilisateur..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Users List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="bg-white rounded-lg border divide-y">
          {filteredUsers.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Aucun utilisateur trouvé
            </div>
          ) : (
            filteredUsers.map((user) => (
              <UserRow
                key={user.id}
                user={user}
                isExpanded={expandedUser === user.id}
                onToggle={() => setExpandedUser(expandedUser === user.id ? null : user.id)}
                onValidate={(depts) => validateMutation.mutate({ userId: user.id, departments: depts })}
                onUpdateUser={(data) => updateUserMutation.mutate({ userId: user.id, data })}
                onUpdatePermission={(dept, perms) => updatePermissionMutation.mutate({ userId: user.id, department: dept, permissions: perms })}
                onDelete={() => {
                  if (confirm(`Supprimer l'utilisateur ${user.cas_login} ?`)) {
                    deleteMutation.mutate(user.id)
                  }
                }}
                isCurrentUser={user.id === currentUser?.id}
                currentUserIsSuperadmin={currentUser?.is_superadmin || false}
                isLoading={validateMutation.isPending || updateUserMutation.isPending || updatePermissionMutation.isPending}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}

interface UserRowProps {
  user: User
  isExpanded: boolean
  onToggle: () => void
  onValidate: (departments: string[]) => void
  onUpdateUser: (data: any) => void
  onUpdatePermission: (department: string, permissions: Partial<DepartmentPermissions>) => void
  onDelete: () => void
  isCurrentUser: boolean
  currentUserIsSuperadmin: boolean
  isLoading: boolean
}

function UserRow({ 
  user, 
  isExpanded, 
  onToggle, 
  onValidate, 
  onUpdateUser,
  onUpdatePermission,
  onDelete,
  isCurrentUser,
  currentUserIsSuperadmin,
  isLoading 
}: UserRowProps) {
  const [selectedDepts, setSelectedDepts] = useState<string[]>(['RT'])
  const [editingDept, setEditingDept] = useState<string | null>(null)
  const [editedPerms, setEditedPerms] = useState<Partial<DepartmentPermissions>>({})

  const handleValidate = () => {
    onValidate(selectedDepts)
  }

  const handleSavePermissions = () => {
    if (editingDept) {
      onUpdatePermission(editingDept, editedPerms)
      setEditingDept(null)
      setEditedPerms({})
    }
  }

  const startEditingDept = (dept: string) => {
    setEditingDept(dept)
    setEditedPerms(user.permissions[dept] || {})
  }

  return (
    <div>
      {/* Main row */}
      <div 
        className={`flex items-center p-4 cursor-pointer hover:bg-gray-50 ${!user.is_active ? 'bg-amber-50' : ''}`}
        onClick={onToggle}
      >
        <div className="mr-3">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900">{user.cas_login}</span>
            {user.is_superadmin && (
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                Superadmin
              </span>
            )}
            {!user.is_active && (
              <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                En attente
              </span>
            )}
            {isCurrentUser && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                Vous
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500">
            {user.prenom} {user.nom} • {user.email || 'Pas d\'email'}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {Object.keys(user.permissions).map(dept => (
            <span key={dept} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
              {dept}
            </span>
          ))}
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t bg-gray-50">
          {/* Pending user validation */}
          {!user.is_active && (
            <div className="mb-4 p-4 bg-amber-100 rounded-lg">
              <h4 className="font-medium text-amber-800 mb-2">Valider ce compte</h4>
              <p className="text-sm text-amber-700 mb-3">
                Sélectionnez les départements auxquels donner accès :
              </p>
              <div className="flex flex-wrap gap-2 mb-3">
                {DEPARTMENTS.map(dept => (
                  <label key={dept} className="flex items-center gap-2 bg-white px-3 py-1 rounded border cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedDepts.includes(dept)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedDepts([...selectedDepts, dept])
                        } else {
                          setSelectedDepts(selectedDepts.filter(d => d !== dept))
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600"
                    />
                    <span className="text-sm">{dept}</span>
                  </label>
                ))}
              </div>
              <button
                onClick={handleValidate}
                disabled={isLoading || selectedDepts.length === 0}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Valider le compte
              </button>
            </div>
          )}

          {/* User info */}
          <div className="grid grid-cols-2 gap-4 mb-4 p-4 bg-white rounded-lg">
            <div>
              <span className="text-sm text-gray-500">Créé le</span>
              <div>{user.date_creation ? new Date(user.date_creation).toLocaleDateString('fr-FR') : '-'}</div>
            </div>
            <div>
              <span className="text-sm text-gray-500">Dernière connexion</span>
              <div>{user.date_derniere_connexion ? new Date(user.date_derniere_connexion).toLocaleDateString('fr-FR') : 'Jamais'}</div>
            </div>
          </div>

          {/* Superadmin toggle (only for superadmins) */}
          {currentUserIsSuperadmin && user.is_active && !isCurrentUser && (
            <div className="mb-4 p-4 bg-white rounded-lg">
              <label className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-purple-600" />
                  <span className="font-medium">Superadmin (accès à tous les départements)</span>
                </div>
                <input
                  type="checkbox"
                  checked={user.is_superadmin}
                  onChange={(e) => onUpdateUser({ is_superadmin: e.target.checked })}
                  className="rounded border-gray-300 text-purple-600 w-5 h-5"
                />
              </label>
            </div>
          )}

          {/* Permissions by department */}
          {user.is_active && (
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Permissions par département</h4>
              {DEPARTMENTS.map(dept => {
                const perms = user.permissions[dept]
                const isEditing = editingDept === dept

                return (
                  <div key={dept} className="bg-white rounded-lg border p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-5 h-5 text-blue-600" />
                        <span className="font-medium">{dept}</span>
                        {perms?.is_dept_admin && (
                          <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                            Admin
                          </span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {isEditing ? (
                          <>
                            <button
                              onClick={handleSavePermissions}
                              disabled={isLoading}
                              className="p-2 bg-green-100 text-green-700 rounded hover:bg-green-200"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {setEditingDept(null); setEditedPerms({})}}
                              className="p-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => startEditingDept(dept)}
                            className="p-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {perms || isEditing ? (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {(Object.keys(PERMISSION_LABELS) as Array<keyof DepartmentPermissions>).map(perm => {
                          const currentValue = isEditing 
                            ? (editedPerms[perm] ?? perms?.[perm] ?? false)
                            : (perms?.[perm] ?? false)

                          return (
                            <label 
                              key={perm}
                              className={`flex items-center gap-2 text-sm p-2 rounded ${
                                isEditing ? 'bg-blue-50 cursor-pointer' : ''
                              }`}
                            >
                              {isEditing ? (
                                <input
                                  type="checkbox"
                                  checked={currentValue}
                                  onChange={(e) => setEditedPerms({ ...editedPerms, [perm]: e.target.checked })}
                                  className="rounded border-gray-300 text-blue-600"
                                />
                              ) : currentValue ? (
                                <Check className="w-4 h-4 text-green-600" />
                              ) : (
                                <X className="w-4 h-4 text-gray-300" />
                              )}
                              <span className={currentValue ? 'text-gray-900' : 'text-gray-400'}>
                                {PERMISSION_LABELS[perm]}
                              </span>
                            </label>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500 flex items-center gap-2">
                        <Eye className="w-4 h-4" />
                        Aucune permission pour ce département
                        <button
                          onClick={() => startEditingDept(dept)}
                          className="text-blue-600 hover:underline"
                        >
                          Ajouter
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {/* Delete button */}
          {!isCurrentUser && (
            <div className="mt-4 pt-4 border-t flex justify-end">
              <button
                onClick={onDelete}
                disabled={isLoading}
                className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-2 rounded-lg"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer l'utilisateur
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
