import { ReactNode } from 'react'
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  suffix?: string
  change?: number
  changeLabel?: string
  icon?: ReactNode
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'orange'
  loading?: boolean
  trend?: { value: number; direction: 'up' | 'down' }
}

const colorClasses = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-green-50 text-green-600',
  yellow: 'bg-yellow-50 text-yellow-600',
  red: 'bg-red-50 text-red-600',
  purple: 'bg-purple-50 text-purple-600',
  orange: 'bg-orange-50 text-orange-600',
}

export default function StatCard({ 
  title, 
  value, 
  subtitle,
  suffix,
  change, 
  changeLabel,
  icon,
  color = 'blue',
  loading = false,
  trend,
}: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          {loading ? (
            <Loader2 className="w-6 h-6 animate-spin text-gray-400 mt-2" />
          ) : (
            <>
              <p className="stat-value mt-1">
                {value}{suffix && <span className="text-lg text-gray-500 ml-1">{suffix}</span>}
              </p>
              {subtitle && (
                <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
              )}
              {change !== undefined && (
                <div className={`flex items-center gap-1 mt-2 ${change >= 0 ? 'stat-change-up' : 'stat-change-down'}`}>
                  {change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  <span>{change >= 0 ? '+' : ''}{change}%</span>
                  {changeLabel && <span className="text-gray-400 font-normal ml-1">{changeLabel}</span>}
                </div>
              )}
              {trend && (
                <div className={`flex items-center gap-1 mt-2 ${trend.direction === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  {trend.direction === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  <span>{trend.value >= 0 ? '+' : ''}{trend.value}</span>
                </div>
              )}
            </>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
