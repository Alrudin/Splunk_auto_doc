import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import RunDetailPage from '../pages/RunDetailPage'
import * as runsApi from '../api/runs'

// Mock the runs API
vi.mock('../api/runs', () => ({
  default: {
    getRun: vi.fn(),
    getParseStatus: vi.fn(),
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
        queries: {
          retry: false,
        },
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const renderWithRouter = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetailPage />} />
          </Routes>
        </BrowserRouter>
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

  it('should display loading state initially', () => {
    vi.mocked(runsApi.default.getRun).mockImplementation(
      () => new Promise(() => {})
    )
    vi.mocked(runsApi.default.getParseStatus).mockImplementation(
      () => new Promise(() => {})
    )

    // Navigate to the route
    window.history.pushState({}, '', '/runs/1')
    renderWithRouter()

    expect(screen.getByText('Loading run details...')).toBeDefined()
  })

  it('should display run details when loaded', async () => {
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
      status: 'complete',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T01:00:00Z',
      file_count: 5,
    }

    const mockParseStatus = {
      run_id: 1,
      status: 'complete',
      error_message: null,
      summary: {
        files_parsed: 5,
        stanzas_created: 100,
        typed_projections: {},
        parse_errors: 0,
        duration_seconds: 30,
      },
    }

    vi.mocked(runsApi.default.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.default.getParseStatus).mockResolvedValue(mockParseStatus)

    window.history.pushState({}, '', '/runs/1')
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Run #1 Details')).toBeDefined()
    })

    expect(screen.getByText('Test Run')).toBeDefined()
    expect(screen.getByText('complete')).toBeDefined()
  })

  it('should display error message when parse fails', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      label: 'Failed Run',
      status: 'failed',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T01:00:00Z',
    }

    const mockParseStatus = {
      run_id: 1,
      status: 'failed',
      error_message: 'Parse error occurred',
      summary: null,
    }

    vi.mocked(runsApi.default.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.default.getParseStatus).mockResolvedValue(mockParseStatus)

    window.history.pushState({}, '', '/runs/1')
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Parse error occurred')).toBeDefined()
    })
  })

  it('should display parsing status with spinner', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      label: 'Parsing Run',
      status: 'parsing',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T01:00:00Z',
    }

    const mockParseStatus = {
      run_id: 1,
      status: 'parsing',
      error_message: null,
      summary: null,
    }

    vi.mocked(runsApi.default.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.default.getParseStatus).mockResolvedValue(mockParseStatus)

    window.history.pushState({}, '', '/runs/1')
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('parsing')).toBeDefined()
    })

    // Check for spinner icon (animate-spin class)
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetailPage />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    )
    window.history.pushState({}, '', '/runs/1')

    await waitFor(() => {
      const spinners = container.querySelectorAll('.animate-spin')
      expect(spinners.length).toBeGreaterThan(0)
    })
  })

  it('should display summary metrics when available', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      label: 'Test Run',
      status: 'complete',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T01:00:00Z',
    }

    const mockParseStatus = {
      run_id: 1,
      status: 'complete',
      error_message: null,
      summary: {
        files_parsed: 10,
        stanzas_created: 200,
        typed_projections: {},
        parse_errors: 2,
        duration_seconds: 60,
      },
    }

    vi.mocked(runsApi.default.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.default.getParseStatus).mockResolvedValue(mockParseStatus)

    window.history.pushState({}, '', '/runs/1')
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('10')).toBeDefined() // files_parsed
      expect(screen.getByText('200')).toBeDefined() // stanzas_created
      expect(screen.getByText('2')).toBeDefined() // parse_errors
    })
  })

  it('should show link back to runs page', async () => {
    const mockRun = {
      id: 1,
      upload_type: 'ds_etc' as const,
      status: 'complete',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T01:00:00Z',
    }

    const mockParseStatus = {
      run_id: 1,
      status: 'complete',
      error_message: null,
      summary: null,
    }

    vi.mocked(runsApi.default.getRun).mockResolvedValue(mockRun)
    vi.mocked(runsApi.default.getParseStatus).mockResolvedValue(mockParseStatus)

    window.history.pushState({}, '', '/runs/1')
    renderWithRouter()

    await waitFor(() => {
      const backLink = screen.getByText('← Back to Runs')
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
