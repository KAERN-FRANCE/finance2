import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '../services/api'
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, Loader } from 'lucide-react'

export default function DocumentsPage() {
  const [uploading, setUploading] = useState(false)
  const queryClient = useQueryClient()

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.list,
  })

  const { data: stats } = useQuery({
    queryKey: ['documents', 'stats'],
    queryFn: documentsApi.getStats,
  })

  const uploadMutation = useMutation({
    mutationFn: documentsApi.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setUploading(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    for (const file of Array.from(files)) {
      await uploadMutation.mutateAsync(file)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'processing':
        return <Loader className="w-5 h-5 text-blue-500 animate-spin" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      default:
        return <FileText className="w-5 h-5 text-gray-400" />
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900">Base de Connaissances</h2>
        <p className="mt-2 text-gray-600">
          Gérez les documents de votre entreprise pour alimenter l'analyse des réunions
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="card">
            <p className="text-sm text-gray-600">Total Documents</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_documents}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600">Taille Totale</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_size_mb.toFixed(1)} MB</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600">Chunks Indexés</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_chunks}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600">Catégories</p>
            <p className="text-2xl font-bold text-gray-900">
              {Object.keys(stats.documents_by_category).length}
            </p>
          </div>
        </div>
      )}

      {/* Upload */}
      <div className="card mb-8">
        <label className="flex flex-col items-center justify-center h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-primary-500 transition-colors">
          <Upload className="w-8 h-8 text-gray-400 mb-2" />
          <span className="text-sm text-gray-600">
            Cliquez pour uploader des documents (PDF, DOCX, CSV, XLSX)
          </span>
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.csv,.xlsx"
            onChange={handleFileUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
        {uploading && (
          <div className="mt-4 text-center text-sm text-gray-600">
            Upload en cours...
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Documents ({documents.length})</h3>
        {isLoading ? (
          <div className="text-center py-8">
            <Loader className="w-8 h-8 animate-spin mx-auto text-gray-400" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Aucun document. Commencez par en uploader.
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center space-x-3 flex-1">
                  {getStatusIcon(doc.status)}
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{doc.filename}</p>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                      <span>{doc.file_type.toUpperCase()}</span>
                      <span>{(doc.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                      <span className="capitalize">{doc.category}</span>
                      <span className="capitalize">{doc.status}</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(doc.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
