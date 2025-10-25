import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import runsApi from '../api/runs'
import StatusBadge from '../components/StatusBadge'

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const runId = id ? parseInt(id, 10) : 0

  // Fetch run details
  const {
    data: run,
    isLoading: runLoading,
    isError: runError,
    error: runErrorDetails,
  } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runsApi.getRun(runId),
    enabled: runId > 0,
  })

  // Fetch run summary
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    error: summaryErrorDetails,
  } = useQuery({
    queryKey: ['run-summary', runId],
    queryFn: () => runsApi.getSummary(runId),
    enabled: runId > 0,
  })

  // Invalid ID
  if (!runId || runId < 1) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-sm text-red-800">
          <strong>Invalid run ID:</strong> {id}
        </p>
        <Link
          to="/runs"
          className="mt-4 inline-flex items-center text-sm text-red-700 hover:text-red-900"
        >
          ← Back to runs
        </Link>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/runs"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <svg
            className="w-4 h-4 mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to runs
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Run Details</h1>
        <p className="mt-2 text-gray-600">
          View details and parsed entity counts for run #{runId}
        </p>
      </div>

      {/* Run Details Card */}
      {runLoading && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex justify-center items-center py-8">
            <svg
              className="animate-spin h-8 w-8 text-primary-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span className="ml-3 text-gray-600">Loading run details...</span>
          </div>
        </div>
      )}

      {runError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-sm text-red-800">
            <strong>Error loading run:</strong>{' '}
            {runErrorDetails instanceof Error
              ? runErrorDetails.message
              : 'An unknown error occurred'}
          </p>
        </div>
      )}

      {run && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Run Information
          </h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Run ID</dt>
              <dd className="mt-1 text-sm text-gray-900">{run.id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <StatusBadge status={run.status} />
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Upload Type</dt>
              <dd className="mt-1 text-sm text-gray-900">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {run.upload_type}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Label</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {run.label || '-'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created At</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(run.created_at).toLocaleString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Updated At</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(run.updated_at).toLocaleString()}
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* Parsed Entity Counts Panel */}
      {summaryLoading && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Parsed Entity Counts
          </h2>
          <div className="flex justify-center items-center py-8">
            <svg
              className="animate-spin h-8 w-8 text-primary-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span className="ml-3 text-gray-600">Loading summary...</span>
          </div>
        </div>
      )}

      {summaryError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">
            <strong>Error loading summary:</strong>{' '}
            {summaryErrorDetails instanceof Error
              ? summaryErrorDetails.message
              : 'An unknown error occurred'}
          </p>
        </div>
      )}

      {summary && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Parsed Entity Counts
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <EntityCountCard
              label="Stanzas"
              count={summary.stanzas}
              icon="📄"
            />
            <EntityCountCard label="Inputs" count={summary.inputs} icon="📥" />
            <EntityCountCard label="Props" count={summary.props} icon="🔧" />
            <EntityCountCard
              label="Transforms"
              count={summary.transforms}
              icon="🔄"
            />
            <EntityCountCard
              label="Indexes"
              count={summary.indexes}
              icon="📊"
            />
            <EntityCountCard
              label="Outputs"
              count={summary.outputs}
              icon="📤"
            />
            <EntityCountCard
              label="Serverclasses"
              count={summary.serverclasses}
              icon="🖥️"
            />
          </div>
        </div>
      )}
    </div>
  )
}

interface EntityCountCardProps {
  label: string
  count: number
  icon: string
}

function EntityCountCard({ label, count, icon }: EntityCountCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-2xl font-bold text-gray-900">{count}</span>
      </div>
      <p className="text-sm font-medium text-gray-600">{label}</p>
    </div>
  )
}
