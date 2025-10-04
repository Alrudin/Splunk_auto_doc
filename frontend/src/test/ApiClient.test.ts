import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ApiClient } from '../api/client'

// Mock fetch globally
global.fetch = vi.fn()

describe('ApiClient', () => {
  let apiClient: ApiClient
  const mockFetch = global.fetch as ReturnType<typeof vi.fn>

  beforeEach(() => {
    apiClient = new ApiClient('/test-api')
    mockFetch.mockClear()
  })

  describe('GET requests', () => {
    it('should make a GET request to the correct endpoint', async () => {
      const mockResponse = { data: 'test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      })

      const result = await apiClient.get('/endpoint')

      expect(mockFetch).toHaveBeenCalledWith(
        '/test-api/endpoint',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle GET request errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Resource not found' }),
      })

      await expect(apiClient.get('/not-found')).rejects.toThrow()
    })
  })

  describe('POST requests', () => {
    it('should make a POST request with JSON body', async () => {
      const mockResponse = { id: 1, created: true }
      const postData = { name: 'test' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      })

      const result = await apiClient.post('/endpoint', postData)

      expect(mockFetch).toHaveBeenCalledWith(
        '/test-api/endpoint',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle POST request errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Invalid data' }),
      })

      await expect(apiClient.post('/endpoint', {})).rejects.toThrow()
    })
  })

  describe('POST form data', () => {
    it('should make a POST request with FormData', async () => {
      const mockResponse = { id: 1, uploaded: true }
      const formData = new FormData()
      formData.append('file', 'test')

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      })

      const result = await apiClient.postFormData('/upload', formData)

      expect(mockFetch).toHaveBeenCalledWith(
        '/test-api/upload',
        expect.objectContaining({
          method: 'POST',
          body: formData,
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error handling', () => {
    it('should handle 204 No Content responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await apiClient.delete('/endpoint')
      expect(result).toEqual({})
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(apiClient.get('/endpoint')).rejects.toThrow('Network error')
    })

    it('should handle non-JSON error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Not JSON')
        },
      })

      await expect(apiClient.get('/endpoint')).rejects.toThrow('500')
    })

    it('should use error detail from response when available', async () => {
      const errorDetail = 'Specific error message'
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        json: async () => ({ detail: errorDetail }),
      })

      await expect(apiClient.get('/endpoint')).rejects.toThrow(errorDetail)
    })
  })

  describe('PUT and DELETE requests', () => {
    it('should make a PUT request', async () => {
      const mockResponse = { updated: true }
      const putData = { name: 'updated' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      })

      const result = await apiClient.put('/endpoint/1', putData)

      expect(mockFetch).toHaveBeenCalledWith(
        '/test-api/endpoint/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should make a DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      await apiClient.delete('/endpoint/1')

      expect(mockFetch).toHaveBeenCalledWith(
        '/test-api/endpoint/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })
  })
})
