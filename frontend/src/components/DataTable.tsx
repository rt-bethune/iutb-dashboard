// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface DataTableProps<T = any> {
  data: T[]
  columns: {
    key: string
    header: string
    render?: (item: T) => React.ReactNode
    align?: 'left' | 'center' | 'right'
  }[]
  emptyMessage?: string
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function DataTable<T = any>({ 
  data, 
  columns,
  emptyMessage = "Aucune donnée"
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            {columns.map((col) => (
              <th 
                key={col.key as string}
                className={`
                  px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider
                  ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                `}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((item, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td 
                  key={col.key as string}
                  className={`
                    px-4 py-3 text-sm text-gray-700
                    ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                  `}
                >
                  {col.render 
                    ? col.render(item) 
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    : String((item as any)[col.key] ?? '-')
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
