import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { meetingsApi } from '../services/api'
import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function MeetingSetupPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    title: '',
    participants: '',
    agenda: '',
    language: 'fr',
  })

  const createMutation = useMutation({
    mutationFn: meetingsApi.create,
    onSuccess: (meeting) => {
      navigate(`/meetings/${meeting.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      title: formData.title,
      participants: formData.participants
        .split(',')
        .map((p) => p.trim())
        .filter(Boolean),
      agenda: formData.agenda || undefined,
      language: formData.language,
    })
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/meetings" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Retour aux réunions
      </Link>

      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Nouvelle Réunion
        </h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="label">Titre de la réunion *</label>
            <input
              type="text"
              required
              className="input"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="ex: Comité de direction Q1"
            />
          </div>

          <div>
            <label className="label">
              Participants (séparés par des virgules) *
            </label>
            <input
              type="text"
              required
              className="input"
              value={formData.participants}
              onChange={(e) =>
                setFormData({ ...formData, participants: e.target.value })
              }
              placeholder="ex: Marie Dupont, Jean Martin, Sophie Bernard"
            />
          </div>

          <div>
            <label className="label">Agenda (optionnel)</label>
            <textarea
              className="input"
              rows={4}
              value={formData.agenda}
              onChange={(e) =>
                setFormData({ ...formData, agenda: e.target.value })
              }
              placeholder="Sujets à aborder durant la réunion..."
            />
          </div>

          <div>
            <label className="label">Langue</label>
            <select
              className="input"
              value={formData.language}
              onChange={(e) =>
                setFormData({ ...formData, language: e.target.value })
              }
            >
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </div>

          <div className="flex justify-end space-x-4">
            <Link to="/meetings" className="btn btn-secondary">
              Annuler
            </Link>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Création...' : 'Créer la réunion'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
