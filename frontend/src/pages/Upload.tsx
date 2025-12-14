import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Upload as UploadIcon, 
  FileText, 
  Trash2, 
  Download, 
  RefreshCw,
  Clock,
  HardDrive,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import FileUpload, { FileType } from '../components/FileUpload'
import { uploadApi } from '../services/api'
import { useDepartment } from '../contexts/DepartmentContext'

interface UploadedFile {
  filename: string
  type: string
  size: number
  modified: string
}

const fileTypeOptions: { value: FileType; label: string; description: string }[] = [
  { value: 'budget', label: '💰 Budget', description: 'Fichiers de suivi budgétaire (Excel)' },
  { value: 'edt', label: '📅 EDT / Charges', description: 'Services enseignants et occupation salles (Excel)' },
  { value: 'parcoursup', label: '🎓 Parcoursup', description: 'Export candidatures Parcoursup (CSV)' },
  { value: 'etudiants', label: '👥 Étudiants', description: 'Liste des étudiants inscrits (CSV/Excel)' },
  { value: 'notes', label: '📝 Notes', description: 'Notes et résultats par module (CSV/Excel)' },
  { value: 'other', label: '📄 Autre', description: 'Autres fichiers (Excel, CSV, PDF)' },
]

export default function UploadPage() {
  const { department } = useDepartment()
  const [activeTab, setActiveTab] = useState<'upload' | 'files'>('upload')
  const [selectedTypes, setSelectedTypes] = useState<FileType[]>(['budget', 'edt', 'parcoursup'])
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  
  const queryClient = useQueryClient()

  // Fetch uploaded files
  const { data: filesData, isLoading: filesLoading, refetch: refetchFiles } = useQuery({
    queryKey: ['uploaded-files', department],
    queryFn: () => uploadApi.listFiles(department),
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: ({ file, type, description }: { file: File; type: FileType; description?: string }) =>
      uploadApi.uploadFile(department, file, type, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploaded-files', department] })
      setNotification({ type: 'success', message: 'Fichier uploadé avec succès!' })
      setTimeout(() => setNotification(null), 5000)
    },
    onError: (error: any) => {
      setNotification({ 
        type: 'error', 
        message: error.response?.data?.detail || 'Erreur lors de l\'upload' 
      })
      setTimeout(() => setNotification(null), 5000)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: ({ filename, type }: { filename: string; type: string }) =>
      uploadApi.deleteFile(department, filename, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploaded-files', department] })
      setNotification({ type: 'success', message: 'Fichier supprimé' })
      setTimeout(() => setNotification(null), 3000)
    },
  })

  const handleUpload = async (file: File, type: FileType, description?: string) => {
    await uploadMutation.mutateAsync({ file, type, description })
  }

  const handleDelete = async (filename: string, type: string) => {
    if (confirm(`Supprimer le fichier "${filename}" ?`)) {
      await deleteMutation.mutateAsync({ filename, type })
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (isoDate: string): string => {
    return new Date(isoDate).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTypeIcon = (type: string): string => {
    const icons: Record<string, string> = {
      budget: '💰',
      edt: '📅',
      parcoursup: '🎓',
      etudiants: '👥',
      notes: '📝',
      other: '📄',
    }
    return icons[type] || '📄'
  }

  const files = filesData?.files || []
  const totalSize = files.reduce((acc: number, f: UploadedFile) => acc + f.size, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📤 Import de fichiers</h1>
          <p className="text-gray-500 mt-1">
            Importez vos données depuis des fichiers Excel ou CSV
          </p>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div className={`
          flex items-center gap-3 p-4 rounded-lg
          ${notification.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}
        `}>
          {notification.type === 'success' 
            ? <CheckCircle className="w-5 h-5" />
            : <AlertCircle className="w-5 h-5" />
          }
          <p>{notification.message}</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{files.length}</p>
            <p className="text-sm text-gray-500">Fichiers uploadés</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
          <div className="p-3 bg-green-50 rounded-lg">
            <HardDrive className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{formatFileSize(totalSize)}</p>
            <p className="text-sm text-gray-500">Espace utilisé</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
          <div className="p-3 bg-purple-50 rounded-lg">
            <Clock className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {files[0] ? formatDate(files[0].modified).split(' ')[0] : '-'}
            </p>
            <p className="text-sm text-gray-500">Dernier upload</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          <button
            onClick={() => setActiveTab('upload')}
            className={`
              py-4 px-1 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'upload'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
          >
            <UploadIcon className="w-4 h-4 inline-block mr-2" />
            Importer des fichiers
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`
              py-4 px-1 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'files'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
          >
            <FileText className="w-4 h-4 inline-block mr-2" />
            Fichiers importés ({files.length})
          </button>
        </nav>
      </div>

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div className="space-y-6">
          {/* Type selector */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Types de fichiers à importer</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {fileTypeOptions.map((option) => (
                <label
                  key={option.value}
                  className={`
                    flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all
                    ${selectedTypes.includes(option.value)
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(option.value)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTypes([...selectedTypes, option.value])
                      } else {
                        setSelectedTypes(selectedTypes.filter(t => t !== option.value))
                      }
                    }}
                    className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <div>
                    <p className="font-medium text-gray-900">{option.label}</p>
                    <p className="text-xs text-gray-500">{option.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Upload zones */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {selectedTypes.map((type) => (
              <FileUpload
                key={type}
                type={type}
                onUpload={handleUpload}
                disabled={uploadMutation.isPending}
              />
            ))}
          </div>

          {/* Help section */}
          <div className="bg-blue-50 rounded-xl p-6">
            <h3 className="font-semibold text-blue-900 mb-3">💡 Conseils d'import</h3>
            <ul className="space-y-2 text-sm text-blue-800">
              <li>• Utilisez les <strong>fichiers templates</strong> disponibles dans <code>/data/examples/</code></li>
              <li>• Les fichiers CSV doivent utiliser le séparateur <strong>point-virgule (;)</strong></li>
              <li>• L'encodage recommandé est <strong>UTF-8</strong></li>
              <li>• La première ligne doit contenir les <strong>en-têtes de colonnes</strong></li>
              <li>• Taille maximum par fichier: <strong>10 MB</strong></li>
            </ul>
          </div>
        </div>
      )}

      {/* Files Tab */}
      {activeTab === 'files' && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Fichiers importés</h3>
            <button
              onClick={() => refetchFiles()}
              disabled={filesLoading}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${filesLoading ? 'animate-spin' : ''}`} />
              Actualiser
            </button>
          </div>

          {filesLoading ? (
            <div className="p-12 text-center">
              <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-500">Chargement...</p>
            </div>
          ) : files.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun fichier importé</p>
              <button
                onClick={() => setActiveTab('upload')}
                className="mt-4 text-primary-600 hover:text-primary-700 font-medium"
              >
                Importer un fichier →
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {files.map((file: UploadedFile) => (
                <div 
                  key={`${file.type}-${file.filename}`}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-2xl">{getTypeIcon(file.type)}</span>
                    <div>
                      <p className="font-medium text-gray-900">{file.filename}</p>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span className="px-2 py-0.5 bg-gray-100 rounded text-xs uppercase">
                          {file.type}
                        </span>
                        <span>{formatFileSize(file.size)}</span>
                        <span>{formatDate(file.modified)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => window.open(`/api/upload/download/${file.type}/${file.filename}`)}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Télécharger"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(file.filename, file.type)}
                      disabled={deleteMutation.isPending}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
