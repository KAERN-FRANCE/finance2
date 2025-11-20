import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '../services/api'
import { ArrowLeft, Download, CheckCircle, XCircle, AlertTriangle, Lightbulb } from 'lucide-react'

export default function ReportPage() {
  const { reportId } = useParams<{ reportId: string }>()

  const { data: report, isLoading } = useQuery({
    queryKey: ['reports', reportId],
    queryFn: () => reportsApi.get(reportId!),
    enabled: !!reportId,
  })

  const handleDownloadMarkdown = async () => {
    if (!reportId) return
    const blob = await reportsApi.downloadMarkdown(reportId)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${reportId}.md`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  if (isLoading || !report) {
    return <div className="max-w-7xl mx-auto px-4 py-8">Chargement du rapport...</div>
  }

  const factCheckSummary = report.metadata?.fact_check_summary || {}

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <Link to="/meetings" className="inline-flex items-center text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour aux réunions
        </Link>
        <button onClick={handleDownloadMarkdown} className="btn btn-secondary inline-flex items-center">
          <Download className="w-4 h-4 mr-2" />
          Télécharger (Markdown)
        </button>
      </div>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Rapport de Réunion</h1>
      <p className="text-gray-600 mb-8">{report.metadata.meeting_title}</p>

      {/* Executive Summary */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Résumé Exécutif</h2>
        <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: report.executive_summary.replace(/\n/g, '<br />') }} />
      </div>

      {/* Fact Checks */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Vérification des Faits</h2>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-700">{factCheckSummary.accurate_statements || 0}</div>
            <div className="text-sm text-gray-600">Affirmations exactes</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-3xl font-bold text-red-700">{factCheckSummary.inaccurate_statements || 0}</div>
            <div className="text-sm text-gray-600">Nécessitent attention</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-blue-700">{factCheckSummary.accuracy_rate || 0}%</div>
            <div className="text-sm text-gray-600">Taux d'exactitude</div>
          </div>
        </div>

        <div className="space-y-4">
          {report.fact_checks.filter(fc => !fc.is_accurate).map((fc, idx) => (
            <div key={idx} className="p-4 bg-orange-50 border-l-4 border-orange-500 rounded">
              <div className="flex items-start">
                <XCircle className="w-5 h-5 text-orange-600 mt-0.5 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-medium text-gray-900 mb-2">{fc.statement}</div>
                  <div className="text-sm text-gray-700 mb-2">{fc.explanation}</div>
                  <div className="text-xs text-gray-600">
                    Confiance: {fc.confidence_score}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Blind Spots */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Analyse des Angles Morts</h2>

        {report.blind_spots.unmentioned_risks && report.blind_spots.unmentioned_risks.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
              Risques Non Mentionnés
            </h3>
            <div className="space-y-3">
              {report.blind_spots.unmentioned_risks.map((risk: any, idx: number) => (
                <div key={idx} className="p-4 bg-red-50 rounded-lg">
                  <div className="font-medium text-gray-900">{risk.type} - {risk.probability}</div>
                  <div className="text-sm text-gray-700 mt-1">{risk.description}</div>
                  <div className="text-sm text-gray-600 mt-1">Impact: {risk.impact}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {report.blind_spots.missed_opportunities && report.blind_spots.missed_opportunities.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <Lightbulb className="w-5 h-5 mr-2 text-yellow-500" />
              Opportunités Manquées
            </h3>
            <div className="space-y-3">
              {report.blind_spots.missed_opportunities.map((opp: any, idx: number) => (
                <div key={idx} className="p-4 bg-yellow-50 rounded-lg">
                  <div className="font-medium text-gray-900">{opp.type}</div>
                  <div className="text-sm text-gray-700 mt-1">{opp.description}</div>
                  <div className="text-sm text-gray-600 mt-1">Valeur: {opp.potential_value}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Recommandations</h2>
        <div className="space-y-6">
          {['high', 'medium', 'low'].map((priority) => {
            const recs = report.recommendations.filter((r: any) => r.priority === priority)
            if (recs.length === 0) return null

            const colors = {
              high: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-700' },
              medium: { bg: 'bg-orange-50', border: 'border-orange-500', text: 'text-orange-700' },
              low: { bg: 'bg-blue-50', border: 'border-blue-500', text: 'text-blue-700' },
            }[priority]

            return (
              <div key={priority}>
                <h3 className={`text-lg font-semibold mb-3 ${colors?.text}`}>
                  Priorité {priority === 'high' ? 'Haute' : priority === 'medium' ? 'Moyenne' : 'Basse'}
                </h3>
                <div className="space-y-3">
                  {recs.map((rec: any, idx: number) => (
                    <div key={idx} className={`p-4 ${colors?.bg} border-l-4 ${colors?.border} rounded`}>
                      <div className="font-medium text-gray-900 mb-2">{rec.title}</div>
                      <div className="text-sm text-gray-700 mb-2">{rec.description}</div>
                      <div className="text-xs text-gray-600">
                        <span className="font-medium">Impact:</span> {rec.expected_impact}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Transcription */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Transcription Complète</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {report.full_transcription.map((segment) => (
            <div key={segment.id} className="p-3 bg-gray-50 rounded text-sm">
              <span className="text-gray-500 mr-2">[{segment.start_time.toFixed(1)}s]</span>
              <span className="text-gray-900">{segment.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
