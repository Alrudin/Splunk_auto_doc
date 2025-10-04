import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import runsApi from '../api/runs'

type UploadType = 'ds_etc' | 'instance_etc' | 'app_bundle' | 'single_conf'

export default function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [uploadType, setUploadType] = useState<UploadType>('instance_etc')
  const [label, setLabel] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const uploadMutation = useMutation({
    mutationFn: ({
      file,
      uploadType,
      label,
    }: {
      file: File
      uploadType: string
      label?: string
    }) => runsApi.uploadFile(file, uploadType, label),
    onSuccess: data => {
      // Navigate to runs page with success message
      navigate(`/runs?success=true&runId=${data.run_id}`)
    },
  })

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (file) {
      uploadMutation.mutate({ file, uploadType, label: label || undefined })
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Upload Configuration
        </h1>
        <p className="mt-2 text-gray-600">
          Upload Splunk configuration files for parsing and analysis
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6"
      >
        {/* Upload Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Type
          </label>
          <select
            value={uploadType}
            onChange={e => setUploadType(e.target.value as UploadType)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-3 py-2 border"
          >
            <option value="instance_etc">Instance etc/ Directory</option>
            <option value="ds_etc">Deployment Server etc/ Directory</option>
            <option value="app_bundle">App Bundle</option>
            <option value="single_conf">Single Conf File</option>
          </select>
          <p className="mt-1 text-sm text-gray-500">
            {uploadType === 'instance_etc' &&
              'Complete Splunk instance etc/ directory structure'}
            {uploadType === 'ds_etc' &&
              'Deployment server etc/ directory structure'}
            {uploadType === 'app_bundle' && 'One or more Splunk apps'}
            {uploadType === 'single_conf' && 'Individual configuration file'}
          </p>
        </div>

        {/* Label Input */}
        <div>
          <label
            htmlFor="label"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Label (Optional)
          </label>
          <input
            type="text"
            id="label"
            value={label}
            onChange={e => setLabel(e.target.value)}
            placeholder="e.g., Production Config 2024-01"
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 px-3 py-2 border"
          />
          <p className="mt-1 text-sm text-gray-500">
            Optional label to help identify this upload
          </p>
        </div>

        {/* File Upload Area */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Configuration File
          </label>
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
              dragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              onChange={handleFileChange}
              accept=".tar,.tar.gz,.tgz,.zip,.conf"
              className="sr-only"
            />
            <label
              htmlFor="file-upload"
              className="flex flex-col items-center cursor-pointer"
            >
              <svg
                className="w-12 h-12 text-gray-400 mb-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="text-sm text-gray-600 mb-1">
                <span className="font-semibold text-primary-500">
                  Click to upload
                </span>{' '}
                or drag and drop
              </p>
              <p className="text-xs text-gray-500">
                TAR, TAR.GZ, ZIP, or CONF files
              </p>
            </label>
          </div>
          {file && (
            <div className="mt-3 flex items-center text-sm text-gray-600">
              <svg
                className="w-5 h-5 text-green-500 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="font-medium">{file.name}</span>
              <span className="ml-2 text-gray-400">
                ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </span>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                Remove
              </button>
            </div>
          )}
        </div>

        {/* Error Display */}
        {uploadMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">
              <strong>Upload failed:</strong>{' '}
              {uploadMutation.error instanceof Error
                ? uploadMutation.error.message
                : 'An unknown error occurred'}
            </p>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!file || uploadMutation.isPending}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {uploadMutation.isPending ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                Uploading...
              </>
            ) : (
              'Upload Configuration'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
