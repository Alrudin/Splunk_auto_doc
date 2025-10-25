import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import RunDetailPage from '../pages/RunDetailPage'
import runsApi from '../api/runs'

// Mock the runsApi module
vi.mock('../api/runs', () => ({
  default: {
    getRun: vi.fn(),
    triggerParse: vi.fn(),
  },
}))

describe('RunDetailPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const renderWithRouter = (runId: string) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/runs/${runId}`]}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('displays loading state initially', () => {
    vi.mocked(runsApi.getRun).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithRouter('1')

    expect(screen.getByText(/Loading run details/i)).toBeDefined()
  })

  it('displays run details when loaded', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      label: 'Test Run',
      status: 'stored',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      file_count: 5,
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    // Wait for the details to load - check for the parse button instead
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Parse Run/i })).toBeDefined()
    })

    // Now check that the data is displayed
    expect(screen.getByText('ds_etc')).toBeDefined()
    expect(screen.getByText('stored')).toBeDefined()
  })

  it('displays error when run fails to load', async () => {
    vi.mocked(runsApi.getRun).mockRejectedValue(new Error('Run not found'))

    renderWithRouter('999')

    await waitFor(() => {
      expect(screen.getByText(/Error loading run/i)).toBeDefined()
    })
    expect(screen.getByText(/Run not found/i)).toBeDefined()
  })

  it('enables parse button for stored runs', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'stored',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    await waitFor(() => {
      const parseButton = screen.getByRole('button', { name: /Parse Run/i })
      expect(parseButton).toBeDefined()
      expect(parseButton.hasAttribute('disabled')).toBe(false)
    })
  })

  it('disables parse button for parsing runs', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'parsing',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    await waitFor(() => {
      const parseButton = screen.getByRole('button', { name: /Parsing.../i })
      expect(parseButton).toBeDefined()
      expect(parseButton.hasAttribute('disabled')).toBe(true)
    })
  })

  it('disables parse button for complete runs', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'complete',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    await waitFor(() => {
      const parseButton = screen.getByRole('button', { name: /Parse Run/i })
      expect(parseButton.hasAttribute('disabled')).toBe(true)
    })

    expect(screen.getByText(/This run has already been parsed/i)).toBeDefined()
  })

  it('disables parse button for normalized runs', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'normalized',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    await waitFor(() => {
      const parseButton = screen.getByRole('button', { name: /Parse Run/i })
      expect(parseButton.hasAttribute('disabled')).toBe(true)
    })

    expect(screen.getByText(/This run has already been parsed/i)).toBeDefined()
  })

  it('disables parse button for failed runs', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'failed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    await waitFor(() => {
      const parseButton = screen.getByRole('button', { name: /Parse Run/i })
      expect(parseButton.hasAttribute('disabled')).toBe(true)
    })

    expect(
      screen.getByText(/Only runs with 'stored' status can be parsed/i)
    ).toBeDefined()
  })

  it('has back to runs link', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'stored',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(runsApi.getRun).mockResolvedValue(mockRun)

    renderWithRouter('1')

    await waitFor(() => {
      const backLink = screen.getByText(/Back to Runs/i)
      expect(backLink).toBeDefined()
      expect(backLink.closest('a')).toHaveProperty('href')
    })
  })
})
