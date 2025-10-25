import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import RunDetailPage from '../pages/RunDetailPage'
import runsApi from '../api/runs'

// Mock the runs API
vi.mock('../api/runs', () => ({
  default: {
    getRun: vi.fn(),
    getSummary: vi.fn(),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/runs/:id" element={children} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('RunDetailPage', () => {
  it('should render loading state initially', () => {
    vi.mocked(runsApi.getRun).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )
    vi.mocked(runsApi.getSummary).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    // Navigate to a specific run ID
    window.history.pushState({}, 'Test', '/runs/123')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Loading run details...')).toBeDefined()
    expect(screen.getByText('Loading summary...')).toBeDefined()
  })

  it('should render run details when data is loaded', async () => {
    const mockRun = {
      id: 123,
      upload_type: 'ds_etc' as const,
      label: 'Test Run',
      status: 'complete',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T01:00:00Z',
    }

    const mockSummary = {
      run_id: 123,
      status: 'complete',
      stanzas: 100,
      inputs: 10,
      props: 20,
      transforms: 15,
      indexes: 5,
      outputs: 8,
      serverclasses: 3,
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.getSummary).mockResolvedValue(mockSummary)

    window.history.pushState({}, 'Test', '/runs/123')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Run Information')).toBeDefined()
    })

    expect(screen.getByText('Test Run')).toBeDefined()
    expect(screen.getByText('ds_etc')).toBeDefined()
  })

  it('should render summary counts when data is loaded', async () => {
    const mockRun = {
      id: 123,
      upload_type: 'ds_etc' as const,
      label: 'Test Run',
      status: 'complete',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T01:00:00Z',
    }

    const mockSummary = {
      run_id: 123,
      status: 'complete',
      stanzas: 100,
      inputs: 10,
      props: 20,
      transforms: 15,
      indexes: 5,
      outputs: 8,
      serverclasses: 3,
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.getSummary).mockResolvedValue(mockSummary)

    window.history.pushState({}, 'Test', '/runs/123')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    // Wait for both run and summary to load
    await waitFor(() => {
      expect(screen.getByText('Parsed Entity Counts')).toBeDefined()
      expect(screen.queryByText('Loading summary...')).toBeNull()
    })

    // Check that all counts are displayed
    expect(screen.getByText('Stanzas')).toBeDefined()
    expect(screen.getByText('Inputs')).toBeDefined()
    expect(screen.getByText('Props')).toBeDefined()
    expect(screen.getByText('Transforms')).toBeDefined()
    expect(screen.getByText('Indexes')).toBeDefined()
    expect(screen.getByText('Outputs')).toBeDefined()
    expect(screen.getByText('Serverclasses')).toBeDefined()

    // Check that count values are displayed
    expect(screen.getByText('100')).toBeDefined() // stanzas
    expect(screen.getByText('10')).toBeDefined() // inputs
    expect(screen.getByText('20')).toBeDefined() // props
    expect(screen.getByText('15')).toBeDefined() // transforms
    expect(screen.getByText('5')).toBeDefined() // indexes
    expect(screen.getByText('8')).toBeDefined() // outputs
    expect(screen.getByText('3')).toBeDefined() // serverclasses
  })

  it('should render error when run fetch fails', async () => {
    vi.mocked(runsApi.getRun).mockRejectedValue(new Error('Run not found'))
    vi.mocked(runsApi.getSummary).mockResolvedValue({
      run_id: 123,
      status: 'complete',
      stanzas: 0,
      inputs: 0,
      props: 0,
      transforms: 0,
      indexes: 0,
      outputs: 0,
      serverclasses: 0,
    })

    window.history.pushState({}, 'Test', '/runs/123')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText(/Error loading run/)).toBeDefined()
    })

    expect(screen.getByText(/Run not found/)).toBeDefined()
  })

  it('should render error when summary fetch fails', async () => {
    const mockRun = {
      id: 123,
      upload_type: 'ds_etc' as const,
      label: 'Test Run',
      status: 'complete',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T01:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.getSummary).mockRejectedValue(
      new Error('Failed to fetch summary')
    )

    window.history.pushState({}, 'Test', '/runs/123')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText(/Error loading summary/)).toBeDefined()
    })

    expect(screen.getByText(/Failed to fetch summary/)).toBeDefined()
  })

  it('should render error for invalid run ID', () => {
    window.history.pushState({}, 'Test', '/runs/invalid')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    expect(screen.getByText(/Invalid run ID/)).toBeDefined()
    expect(screen.getByText(/Back to runs/)).toBeDefined()
  })

  it('should have back to runs link', async () => {
    const mockRun = {
      id: 123,
      upload_type: 'ds_etc' as const,
      label: 'Test Run',
      status: 'complete',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T01:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.getSummary).mockResolvedValue({
      run_id: 123,
      status: 'complete',
      stanzas: 0,
      inputs: 0,
      props: 0,
      transforms: 0,
      indexes: 0,
      outputs: 0,
      serverclasses: 0,
    })

    window.history.pushState({}, 'Test', '/runs/123')

    render(<RunDetailPage />, { wrapper: createWrapper() })

    const backLinks = screen.getAllByText(/Back to runs/)
    expect(backLinks.length).toBeGreaterThan(0)
    expect(backLinks[0].closest('a')).toHaveProperty('href')
  })
})
