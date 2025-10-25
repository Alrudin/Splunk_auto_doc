/**
 * Type definitions for API requests and responses
 */

export type UploadType =
  | 'ds_etc'
  | 'instance_etc'
  | 'app_bundle'
  | 'single_conf'

export interface IngestionRun {
  id: number
  upload_type: UploadType
  label?: string
  status: string
  created_at: string
  updated_at: string
  file_count?: number
}

export interface UploadResponse {
  run_id: number
  upload_type: UploadType
  label?: string
  file_count: number
  message: string
}

export interface HealthResponse {
  status: string
  database?: string
  timestamp?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface ParseStatusResponse {
  run_id: number
  status: string
  error_message?: string | null
  summary?: {
    files_parsed: number
    stanzas_created: number
    typed_projections: Record<string, number>
    parse_errors: number
    duration_seconds: number
  } | null
export interface ParseResponse {
  run_id: number
  status: string
  task_id: string
  message: string
}
