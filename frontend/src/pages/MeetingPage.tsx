import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { meetingsApi } from '../services/api'
import { ArrowLeft, Mic, Square, FileText, AlertTriangle } from 'lucide-react'

export default function MeetingPage() {
  const { meetingId } = useParams<{ meetingId: string }>()
  const navigate = useNavigate()
  const [isRecording, setIsRecording] = useState(false)
  const [transcription, setTranscription] = useState<Array<{ timestamp: number; text: string }>>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const startTimeRef = useRef<number>(0)

  const { data: meeting } = useQuery({
    queryKey: ['meetings', meetingId],
    queryFn: () => meetingsApi.get(meetingId!),
    enabled: !!meetingId,
  })

  const startMutation = useMutation({
    mutationFn: () => meetingsApi.start(meetingId!),
  })

  const stopMutation = useMutation({
    mutationFn: () => meetingsApi.stop(meetingId!),
  })

  const generateReportMutation = useMutation({
    mutationFn: () => meetingsApi.generateReport(meetingId!),
    onSuccess: (data) => {
      navigate(`/reports/${data.report_id}`)
    },
  })

  useEffect(() => {
    if (!meetingId || meeting?.status !== 'in_progress') return

    // Connect WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/meeting/${meetingId}`)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'transcription') {
        setTranscription((prev) => [...prev, message.data])
      } else if (message.type === 'alert') {
        setAlerts((prev) => [...prev, message.data])
      }
    }

    wsRef.current = ws

    return () => {
      ws.close()
    }
  }, [meetingId, meeting?.status])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const chunks: Blob[] = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        const currentTime = (Date.now() - startTimeRef.current) / 1000

        try {
          await meetingsApi.uploadAudio(meetingId!, audioBlob, currentTime - 30)
        } catch (error) {
          console.error('Error uploading audio:', error)
        }

        chunks.length = 0
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()

      // Send chunks every 30 seconds
      const interval = setInterval(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
          mediaRecorder.start()
        }
      }, 30000)

      await startMutation.mutateAsync()
      setIsRecording(true)
      startTimeRef.current = Date.now()

      return () => clearInterval(interval)
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('Impossible d\'accéder au microphone')
    }
  }

  const stopRecording = async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
    }

    await stopMutation.mutateAsync()
    setIsRecording(false)
  }

  if (!meeting) {
    return <div className="max-w-7xl mx-auto px-4 py-8">Chargement...</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/meetings" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Retour
      </Link>

      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">{meeting.title}</h2>
        <p className="text-gray-600 mt-2">
          {meeting.participants.join(', ')}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recording Control */}
          <div className="card">
            <div className="text-center">
              {meeting.status === 'scheduled' || meeting.status === 'in_progress' ? (
                <>
                  {!isRecording ? (
                    <button
                      onClick={startRecording}
                      className="btn btn-primary inline-flex items-center px-8 py-4 text-lg"
                      disabled={startMutation.isPending}
                    >
                      <Mic className="w-6 h-6 mr-3" />
                      Démarrer l'enregistrement
                    </button>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center space-x-2 text-red-600">
                        <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                        <span className="font-medium">Enregistrement en cours...</span>
                      </div>
                      <button
                        onClick={stopRecording}
                        className="btn btn-danger inline-flex items-center px-8 py-4"
                        disabled={stopMutation.isPending}
                      >
                        <Square className="w-5 h-5 mr-2" />
                        Arrêter
                      </button>
                    </div>
                  )}
                </>
              ) : meeting.status === 'completed' ? (
                <button
                  onClick={() => generateReportMutation.mutate()}
                  className="btn btn-primary inline-flex items-center px-8 py-4 text-lg"
                  disabled={generateReportMutation.isPending}
                >
                  <FileText className="w-6 h-6 mr-3" />
                  {generateReportMutation.isPending ? 'Génération...' : 'Générer le rapport'}
                </button>
              ) : null}
            </div>
          </div>

          {/* Transcription */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Transcription</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {transcription.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  La transcription apparaîtra ici en temps réel
                </p>
              ) : (
                transcription.map((item, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded">
                    <span className="text-xs text-gray-500 mr-2">
                      [{item.timestamp.toFixed(1)}s]
                    </span>
                    <span className="text-gray-900">{item.text}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-orange-500" />
            Alertes ({alerts.length})
          </h3>
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {alerts.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">
                Les alertes apparaîtront ici
              </p>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded border-l-4 ${
                    alert.severity === 'critical'
                      ? 'bg-red-50 border-red-500'
                      : alert.severity === 'warning'
                      ? 'bg-orange-50 border-orange-500'
                      : 'bg-blue-50 border-blue-500'
                  }`}
                >
                  <div className="text-xs text-gray-500 mb-1">
                    [{alert.timestamp.toFixed(1)}s]
                  </div>
                  <div className="text-sm font-medium text-gray-900 mb-1">
                    {alert.issue}
                  </div>
                  <div className="text-xs text-gray-600">{alert.statement}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
