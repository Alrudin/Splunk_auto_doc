import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import runsApi from '../api/runs'
import { useState } from 'react'

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [parseError, setParseError] = useState<string | null>(null)

  const runId = id ? parseInt(id, 10) : 0

  // Fetch run details
  const {
    data: run,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runsApi.getRun(runId),
    enabled: runId > 0,
  })

  // Parse mutation
  const parseMutation = useMutation({
    mutationFn: (runId: number) => runsApi.triggerParse(runId),
    onSuccess: () => {
      setParseError(null)
      // Invalidate and refetch run data
      queryClient.invalidateQueries({ queryKey: ['run', runId] })
    },
    onError: (error: Error) => {
      setParseError(error.message)
    },
  })

  const handleParse = () => {
    if (run) {
      parseMutation.mutate(run.id)
    }
  }

  // Determine if parse button should be enabled
  const canParse = run?.status === 'stored'
  const isParsing = parseMutation.isPending || run?.status === 'parsing'
  const isComplete = run?.status === 'normalized' || run?.status === 'complete'

  return (
    <div>
      <div className="mb-8">
        <Link
          to="/runs"
          className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 mb-4"
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
          Back to Runs
        </Link>

        <h1 className="text-3xl font-bold text-gray-900">
          Run Details - ID {runId}
        </h1>
        <p className="mt-2 text-gray-600">
          View details and manage this ingestion run
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
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
      )}

      {/* Error State */}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">
            <strong>Error loading run:</strong>{' '}
            {error instanceof Error
              ? error.message
              : 'An unknown error occurred'}
          </p>
        </div>
      )}

      {/* Run Details */}
      {run && (
        <div className="space-y-6">
          {/* Parse Error Message */}
          {parseError && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">
                <strong>Parse Error:</strong> {parseError}
              </p>
            </div>
          )}

          {/* Parse Success Message */}
          {parseMutation.isSuccess && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <p className="text-sm text-green-800">
                <strong>Parse job started successfully!</strong> The run is now
                being processed.
              </p>
            </div>
          )}

          {/* Run Information Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Run Information
            </h2>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">Run ID</dt>
                <dd className="mt-1 text-sm text-gray-900">{run.id}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Type</dt>
                <dd className="mt-1">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {run.upload_type}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1">
                  <StatusBadge status={run.status} />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Label</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {run.label || '-'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(run.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  File Count
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {run.file_count ?? '-'}
                </dd>
              </div>
            </dl>
          </div>

          {/* Actions Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Actions
            </h2>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleParse}
                disabled={!canParse || isParsing || isComplete}
                className={`inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 ${
                  canParse && !isParsing && !isComplete
                    ? 'bg-primary-500 hover:bg-primary-600'
                    : 'bg-gray-300 cursor-not-allowed'
                }`}
              >
                {isParsing && (
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                )}
                {isParsing ? 'Parsing...' : 'Parse Run'}
              </button>
              {!canParse && !isParsing && !isComplete && (
                <p className="text-sm text-gray-500">
                  Only runs with 'stored' status can be parsed.
                </p>
              )}
              {isComplete && (
                <p className="text-sm text-gray-500">
                  This run has already been parsed.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
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
      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
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
      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
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
  if (
    statusLower === 'complete' ||
    statusLower === 'normalized' ||
    statusLower === 'success'
  ) {
    colorClasses = 'bg-green-100 text-green-800'
  } else if (
    statusLower === 'pending' ||
    statusLower === 'stored' ||
    statusLower === 'parsing'
  ) {
    colorClasses = 'bg-yellow-100 text-yellow-800'
  } else if (statusLower === 'failed' || statusLower === 'error') {
    colorClasses = 'bg-red-100 text-red-800'
  }

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClasses}`}
    >
      {icon}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses}`}
    >
      {status}
    </span>
  )
}
