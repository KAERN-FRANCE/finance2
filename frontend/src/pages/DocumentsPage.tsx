import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '../services/api'
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, Loader, Plus, X } from 'lucide-react'

export default function DocumentsPage() {
  const [uploading, setUploading] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [problematiques, setProblematiques] = useState<string[]>([''])
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
    mutationFn: ({ file, problematiques }: { file: File; problematiques: string[] }) =>
      documentsApi.upload(file, problematiques),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setUploading(false)
      setShowUploadModal(false)
      setSelectedFile(null)
      setProblematiques([''])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setSelectedFile(files[0])
    setShowUploadModal(true)
    e.target.value = '' // Reset input
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    const validProblematiques = problematiques.filter(p => p.trim() !== '')
    await uploadMutation.mutateAsync({
      file: selectedFile,
      problematiques: validProblematiques
    })
  }

  const addProblematique = () => {
    setProblematiques([...problematiques, ''])
  }

  const updateProblematique = (index: number, value: string) => {
    const newProblematiques = [...problematiques]
    newProblematiques[index] = value
    setProblematiques(newProblematiques)
  }

  const removeProblematique = (index: number) => {
    setProblematiques(problematiques.filter((_, i) => i !== index))
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
            accept=".pdf,.docx,.csv,.xlsx"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>

      {/* Upload Modal */}
      {showUploadModal && selectedFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4">Upload de document</h3>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Fichier sélectionné :</p>
              <p className="font-medium">{selectedFile.name}</p>
            </div>

            <div className="mb-4">
              <label className="label">
                Problématiques liées à ce document (optionnel)
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Ajoutez des questions ou problématiques que ce document peut aider à résoudre
              </p>

              {problematiques.map((prob, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={prob}
                    onChange={(e) => updateProblematique(index, e.target.value)}
                    className="input flex-1"
                    placeholder="Ex: Quelle est notre marge opérationnelle Q1?"
                  />
                  {problematiques.length > 1 && (
                    <button
                      onClick={() => removeProblematique(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  )}
                </div>
              ))}

              <button
                onClick={addProblematique}
                className="btn btn-secondary inline-flex items-center mt-2"
              >
                <Plus className="w-4 h-4 mr-2" />
                Ajouter une problématique
              </button>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowUploadModal(false)
                  setSelectedFile(null)
                  setProblematiques([''])
                }}
                className="btn btn-secondary"
                disabled={uploading}
              >
                Annuler
              </button>
              <button
                onClick={handleUpload}
                className="btn btn-primary"
                disabled={uploading}
              >
                {uploading ? 'Upload en cours...' : 'Uploader'}
              </button>
            </div>
          </div>
        </div>
      )}

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
                className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-start space-x-3 flex-1">
                  {getStatusIcon(doc.status)}
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{doc.filename}</p>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                      <span>{doc.file_type.toUpperCase()}</span>
                      <span>{(doc.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                      <span className="capitalize">{doc.category}</span>
                      <span className="capitalize">{doc.status}</span>
                    </div>
                    {doc.problematiques && doc.problematiques.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-gray-700 mb-1">Problématiques :</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {doc.problematiques.map((prob, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-primary-600 mr-1">•</span>
                              <span>{prob}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(doc.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg ml-4"
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
