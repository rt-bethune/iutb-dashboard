import { ReactNode, useRef } from 'react'
import { Loader2 } from 'lucide-react'
import ExportButton from './ExportButton'

export interface ChartContainerProps {
  title: string
  subtitle?: string
  children: ReactNode
  actions?: ReactNode
  exportFilename?: string
  showExport?: boolean
  loading?: boolean
  height?: string
}

export default function ChartContainer({ 
  title, 
  subtitle, 
  children, 
  actions,
  exportFilename,
  showExport = true,
  loading = false,
  height = 'h-72',
}: ChartContainerProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {actions}
          {showExport && (
            <ExportButton 
              chartRef={chartRef} 
              filename={exportFilename || title.toLowerCase().replace(/\s+/g, '-')} 
              title={title}
            />
          )}
        </div>
      </div>
      <div className={height} ref={chartRef}>
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  )
}
