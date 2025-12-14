import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export type Department = 'RT' | 'GEII' | 'GCCD' | 'GMP' | 'QLIO' | 'CHIMIE'

export const DEPARTMENTS: Department[] = ['RT', 'GEII', 'GCCD', 'GMP', 'QLIO', 'CHIMIE']

export const DEPARTMENT_NAMES: Record<Department, string> = {
  RT: 'Réseaux & Télécoms',
  GEII: 'Génie Électrique',
  GCCD: 'Génie Civil',
  GMP: 'Génie Mécanique',
  QLIO: 'Qualité Logistique',
  CHIMIE: 'Chimie',
}

interface DepartmentContextType {
  department: Department
  setDepartment: (dept: Department) => void
  departmentName: string
}

const DepartmentContext = createContext<DepartmentContextType | undefined>(undefined)

const STORAGE_KEY = 'selected_department'

export function DepartmentProvider({ children }: { children: ReactNode }) {
  const [department, setDepartmentState] = useState<Department>(() => {
    // Initialize from localStorage or default to RT
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && DEPARTMENTS.includes(stored as Department)) {
      return stored as Department
    }
    return 'RT'
  })

  const setDepartment = (dept: Department) => {
    setDepartmentState(dept)
    localStorage.setItem(STORAGE_KEY, dept)
  }

  const departmentName = DEPARTMENT_NAMES[department]

  return (
    <DepartmentContext.Provider value={{ department, setDepartment, departmentName }}>
      {children}
    </DepartmentContext.Provider>
  )
}

export function useDepartment() {
  const context = useContext(DepartmentContext)
  if (context === undefined) {
    throw new Error('useDepartment must be used within a DepartmentProvider')
  }
  return context
}
