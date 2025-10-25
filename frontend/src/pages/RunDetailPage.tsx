import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import runsApi from '../api/runs'

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>()

  const runIdNumber = runId ? parseInt(runId, 10) : 0

  // Fetch run details
  const {
    data: run,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['run', runIdNumber],
    queryFn: () => runsApi.getRun(runIdNumber),
    enabled: runIdNumber > 0,
  })

  // Fetch parse status with polling
  const { data: parseStatus } = useQuery({
    queryKey: ['parseStatus', runIdNumber],
    queryFn: () => runsApi.getParseStatus(runIdNumber),
    enabled: runIdNumber > 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      // Poll every 2 seconds while parsing
      if (status === 'parsing' || status === 'normalized') {
        return 2000
      }
      // Stop polling for terminal states
      return false
    },
  })

  if (!runId || runIdNumber <= 0) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-sm text-red-800">Invalid run ID</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
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
    )
  }

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-sm text-red-800">
          <strong>Error loading run:</strong>{' '}
          {error instanceof Error ? error.message : 'An unknown error occurred'}
        </p>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <p className="text-sm text-yellow-800">Run not found</p>
      </div>
    )
  }

  const currentStatus = parseStatus?.status || run.status

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="mb-4 text-sm">
        <Link to="/runs" className="text-primary-600 hover:text-primary-800">
          ← Back to Runs
        </Link>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Run #{run.id} Details
        </h1>
        {run.label && (
          <p className="mt-2 text-gray-600 text-lg">{run.label}</p>
        )}
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Status</h2>
          <StatusBadge status={currentStatus} />
        </div>

        {parseStatus?.error_message && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">
              <strong>Error:</strong> {parseStatus.error_message}
            </p>
          </div>
        )}

        {parseStatus?.summary && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-md p-3">
              <p className="text-sm text-gray-600">Files Parsed</p>
              <p className="text-2xl font-bold text-gray-900">
                {parseStatus.summary.files_parsed}
              </p>
            </div>
            <div className="bg-gray-50 rounded-md p-3">
              <p className="text-sm text-gray-600">Stanzas Created</p>
              <p className="text-2xl font-bold text-gray-900">
                {parseStatus.summary.stanzas_created}
              </p>
            </div>
            <div className="bg-gray-50 rounded-md p-3">
              <p className="text-sm text-gray-600">Parse Errors</p>
              <p className="text-2xl font-bold text-gray-900">
                {parseStatus.summary.parse_errors}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Run Details Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Run Information
        </h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Run ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{run.id}</dd>
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
          {run.file_count !== undefined && (
            <div>
              <dt className="text-sm font-medium text-gray-500">File Count</dt>
              <dd className="mt-1 text-sm text-gray-900">{run.file_count}</dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  )
}

interface StatusBadgeProps {
  status: string
}

function StatusBadge({ status }: StatusBadgeProps) {
  const statusLower = status.toLowerCase()

  let colorClasses = 'bg-gray-100 text-gray-800'
  let icon = null

  if (statusLower === 'complete') {
    colorClasses = 'bg-green-100 text-green-800'
    icon = (
      <svg
        className="w-4 h-4 mr-1"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
          clipRule="evenodd"
        />
      </svg>
    )
  } else if (statusLower === 'failed') {
    colorClasses = 'bg-red-100 text-red-800'
    icon = (
      <svg
        className="w-4 h-4 mr-1"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
          clipRule="evenodd"
        />
      </svg>
    )
  } else if (statusLower === 'parsing' || statusLower === 'normalized') {
    colorClasses = 'bg-blue-100 text-blue-800'
    icon = (
      <svg
        className="animate-spin w-4 h-4 mr-1"
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
    )
  } else if (statusLower === 'stored' || statusLower === 'pending') {
    colorClasses = 'bg-yellow-100 text-yellow-800'
  }

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClasses}`}
    >
      {icon}
      {status}
    </span>
  )
}
