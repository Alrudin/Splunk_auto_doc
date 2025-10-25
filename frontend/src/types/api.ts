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

export interface RunSummary {
  run_id: number
  status: string
  stanzas: number
  inputs: number
  props: number
  transforms: number
  indexes: number
  outputs: number
  serverclasses: number
}
