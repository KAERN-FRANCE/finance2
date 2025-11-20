import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { meetingsApi } from '../services/api'
import { Plus, Video, Clock, Users } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'

export default function MeetingsListPage() {
  const { data: meetings = [], isLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: meetingsApi.list,
  })

  const getStatusBadge = (status: string) => {
    const styles = {
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800',
    }
    return styles[status as keyof typeof styles] || styles.scheduled
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Réunions</h2>
          <p className="mt-2 text-gray-600">Gérez et analysez vos réunions</p>
        </div>
        <Link to="/meetings/new" className="btn btn-primary flex items-center">
          <Plus className="w-5 h-5 mr-2" />
          Nouvelle Réunion
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Chargement...</div>
      ) : meetings.length === 0 ? (
        <div className="card text-center py-12">
          <Video className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Aucune réunion
          </h3>
          <p className="text-gray-600 mb-6">
            Créez votre première réunion pour commencer
          </p>
          <Link to="/meetings/new" className="btn btn-primary inline-flex items-center">
            <Plus className="w-5 h-5 mr-2" />
            Créer une réunion
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {meetings.map((meeting) => (
            <Link
              key={meeting.id}
              to={`/meetings/${meeting.id}`}
              className="card hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {meeting.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(meeting.status)}`}>
                      {meeting.status}
                    </span>
                  </div>

                  <div className="flex items-center space-x-6 text-sm text-gray-600">
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {formatDistanceToNow(new Date(meeting.date), { addSuffix: true, locale: fr })}
                    </div>
                    <div className="flex items-center">
                      <Users className="w-4 h-4 mr-1" />
                      {meeting.participants.length} participants
                    </div>
                    {meeting.duration > 0 && (
                      <div>
                        Durée: {Math.floor(meeting.duration / 60)} min
                      </div>
                    )}
                  </div>

                  {meeting.agenda && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                      {meeting.agenda}
                    </p>
                  )}
                </div>

                {meeting.alert_count > 0 && (
                  <div className="ml-4 text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {meeting.alert_count}
                    </div>
                    <div className="text-xs text-gray-500">Alertes</div>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
