import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import App from '../App'
import MainLayout from '../layouts/MainLayout'
import HomePage from '../pages/HomePage'

describe('Navigation and Routing', () => {
  it('should render HomePage at root path', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText('Welcome to Splunk Auto Doc')).toBeDefined()
  })

  it('should render MainLayout with navigation', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    // Check that MainLayout navigation elements are present
    expect(screen.getByText('Home')).toBeDefined()
    expect(screen.getByText('Upload')).toBeDefined()
    expect(screen.getByText('Runs')).toBeDefined()
  })

  it('should have correct link structure in HomePage', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    // Get all links
    const links = container.querySelectorAll('a')

    // Should have multiple links (navigation + page content)
    expect(links.length).toBeGreaterThan(0)

    // Check that some links point to expected routes
    const linkHrefs = Array.from(links).map(link => link.getAttribute('href'))
    expect(linkHrefs.some(href => href === '/')).toBe(true)
    expect(linkHrefs.some(href => href === '/upload')).toBe(true)
    expect(linkHrefs.some(href => href === '/runs')).toBe(true)
  })

  it('should integrate App component with router', () => {
    render(<App />)

    // Should render the app without errors
    // Check for MainLayout elements
    expect(screen.getByText('Splunk Auto Doc')).toBeDefined()
  })

  it('should render correct page title in HomePage within full app', () => {
    render(<App />)

    // Default route should show HomePage
    expect(screen.getByText('Welcome to Splunk Auto Doc')).toBeDefined()
  })
})
