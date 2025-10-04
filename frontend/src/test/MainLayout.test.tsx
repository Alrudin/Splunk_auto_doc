import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'

describe('MainLayout', () => {
  it('should render the brand/logo', () => {
    render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Splunk Auto Doc')).toBeDefined()
  })

  it('should render navigation links', () => {
    render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )
    
    // Check for main navigation links
    const homeLink = screen.getByText('Home')
    const uploadLink = screen.getByText('Upload')
    const runsLink = screen.getByText('Runs')
    
    expect(homeLink).toBeDefined()
    expect(uploadLink).toBeDefined()
    expect(runsLink).toBeDefined()
  })

  it('should render API Docs link', () => {
    render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )
    
    const apiDocsLink = screen.getByText('API Docs')
    expect(apiDocsLink).toBeDefined()
    
    // Check it's an external link
    const anchor = apiDocsLink.closest('a')
    expect(anchor).toBeDefined()
    expect(anchor?.getAttribute('target')).toBe('_blank')
    expect(anchor?.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it('should have correct structure with navbar and main content', () => {
    const { container } = render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )
    
    // Check for navbar
    const nav = container.querySelector('nav')
    expect(nav).toBeDefined()
    
    // Check for main content area
    const main = container.querySelector('main')
    expect(main).toBeDefined()
  })

  it('should apply correct CSS classes for layout', () => {
    const { container } = render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )
    
    // Check root div has min-h-screen class
    const rootDiv = container.firstChild as HTMLElement
    expect(rootDiv.className).toContain('min-h-screen')
  })

  it('should have correct navigation structure', () => {
    const { container } = render(
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    )
    
    // Check that navigation links are inside nav element
    const nav = container.querySelector('nav')
    expect(nav).toBeDefined()
    
    const navLinks = nav?.querySelectorAll('a')
    expect(navLinks?.length).toBeGreaterThan(0)
  })
})
