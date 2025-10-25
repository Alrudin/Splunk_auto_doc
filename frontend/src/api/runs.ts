/**
 * API service functions for ingestion runs
 */
import apiClient from './client'
import type {
  IngestionRun,
  UploadResponse,
  PaginatedResponse,
  ParseResponse,
} from '../types/api'

export const runsApi = {
  /**
   * Get all ingestion runs
   */
  async getRuns(
    page = 1,
    perPage = 20
  ): Promise<PaginatedResponse<IngestionRun>> {
    return apiClient.get<PaginatedResponse<IngestionRun>>(
      `/v1/runs?page=${page}&per_page=${perPage}`
    )
  },

  /**
   * Get a specific ingestion run by ID
   */
  async getRun(runId: number): Promise<IngestionRun> {
    return apiClient.get<IngestionRun>(`/v1/runs/${runId}`)
  },

  /**
   * Upload a file and create a new ingestion run
   */
  async uploadFile(
    file: File,
    uploadType: string,
    label?: string
  ): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('upload_type', uploadType)
    if (label) {
      formData.append('label', label)
    }

    return apiClient.postFormData<UploadResponse>('/v1/uploads', formData)
  },

  /**
   * Trigger parsing for a specific ingestion run
   */
  async triggerParse(runId: number): Promise<ParseResponse> {
    return apiClient.post<ParseResponse>(`/v1/runs/${runId}/parse`, {})
  },
}

export default runsApi
