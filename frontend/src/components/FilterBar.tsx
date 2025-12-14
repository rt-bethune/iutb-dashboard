import { useState, useCallback } from 'react'
import { Filter, X, Calendar, ChevronDown } from 'lucide-react'

export interface FilterOption {
  value: string
  label: string
}

export interface FilterConfig {
  key: string
  label: string
  type: 'select' | 'multiselect' | 'daterange' | 'search'
  options?: FilterOption[]
  placeholder?: string
}

export interface FilterValues {
  [key: string]: string | string[] | { start?: string; end?: string }
}

interface FilterBarProps {
  filters: FilterConfig[]
  values: FilterValues
  onChange: (values: FilterValues) => void
  onReset?: () => void
}

export default function FilterBar({ filters, values, onChange, onReset }: FilterBarProps) {
  const [expanded, setExpanded] = useState(false)

  const handleChange = useCallback((key: string, value: string | string[] | { start?: string; end?: string }) => {
    onChange({ ...values, [key]: value })
  }, [values, onChange])

  const hasActiveFilters = Object.values(values).some(v => 
    v && (Array.isArray(v) ? v.length > 0 : typeof v === 'object' ? v.start || v.end : v !== '')
  )

  const handleReset = () => {
    const emptyValues: FilterValues = {}
    filters.forEach(f => {
      if (f.type === 'multiselect') emptyValues[f.key] = []
      else if (f.type === 'daterange') emptyValues[f.key] = {}
      else emptyValues[f.key] = ''
    })
    onChange(emptyValues)
    onReset?.()
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-500" />
          <span className="font-medium text-gray-700">Filtres</span>
          {hasActiveFilters && (
            <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">
              Actifs
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleReset()
              }}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Réinitialiser
            </button>
          )}
          <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {/* Filters content */}
      {expanded && (
        <div className="border-t border-gray-200 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {filters.map(filter => (
              <FilterField
                key={filter.key}
                config={filter}
                value={values[filter.key]}
                onChange={(value) => handleChange(filter.key, value)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface FilterFieldProps {
  config: FilterConfig
  value: string | string[] | { start?: string; end?: string } | undefined
  onChange: (value: string | string[] | { start?: string; end?: string }) => void
}

function FilterField({ config, value, onChange }: FilterFieldProps) {
  const { type, label, options, placeholder } = config

  if (type === 'select') {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <select
          value={(value as string) || ''}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">{placeholder || 'Tous'}</option>
          {options?.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    )
  }

  if (type === 'multiselect') {
    const selected = (value as string[]) || []
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <div className="space-y-1 max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-2">
          {options?.map(opt => (
            <label key={opt.value} className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(opt.value)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onChange([...selected, opt.value])
                  } else {
                    onChange(selected.filter(v => v !== opt.value))
                  }
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>
    )
  }

  if (type === 'daterange') {
    const dateValue = (value as { start?: string; end?: string }) || {}
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Calendar className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={dateValue.start || ''}
              onChange={(e) => onChange({ ...dateValue, start: e.target.value })}
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              placeholder="Début"
            />
          </div>
          <div className="flex-1 relative">
            <Calendar className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={dateValue.end || ''}
              onChange={(e) => onChange({ ...dateValue, end: e.target.value })}
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              placeholder="Fin"
            />
          </div>
        </div>
      </div>
    )
  }

  if (type === 'search') {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <input
          type="text"
          value={(value as string) || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder || 'Rechercher...'}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        />
      </div>
    )
  }

  return null
}

// Preset period selectors
export function PeriodSelector({ 
  value, 
  onChange,
  options = defaultPeriodOptions 
}: { 
  value: string
  onChange: (value: string) => void
  options?: FilterOption[]
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-500">Période:</span>
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {options.map(opt => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              value === opt.value
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

const defaultPeriodOptions: FilterOption[] = [
  { value: 'current', label: 'Année courante' },
  { value: 'last', label: 'Année précédente' },
  { value: '3years', label: '3 ans' },
  { value: '5years', label: '5 ans' },
  { value: 'all', label: 'Tout' },
]

// Year selector
export function YearSelector({
  value,
  onChange,
  startYear = 2020,
  endYear = new Date().getFullYear()
}: {
  value: string
  onChange: (value: string) => void
  startYear?: number
  endYear?: number
}) {
  const years = []
  for (let y = endYear; y >= startYear; y--) {
    years.push(y)
  }

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
    >
      <option value="">Toutes les années</option>
      {years.map(year => (
        <option key={year} value={`${year}-${year + 1}`}>{year}-{year + 1}</option>
      ))}
    </select>
  )
}
