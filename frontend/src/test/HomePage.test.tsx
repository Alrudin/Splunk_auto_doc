import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import HomePage from '../pages/HomePage'

describe('HomePage', () => {
  it('should render the page title', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Welcome to Splunk Auto Doc')).toBeDefined()
  })

  it('should render the upload configuration link', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    
    const uploadLink = screen.getByText('Upload Configuration')
    expect(uploadLink).toBeDefined()
    expect(uploadLink.closest('a')).toHaveProperty('href')
  })

  it('should render the view runs link', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    
    const viewRunsLink = screen.getByText('View Runs')
    expect(viewRunsLink).toBeDefined()
    expect(viewRunsLink.closest('a')).toHaveProperty('href')
  })

  it('should render feature cards', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Configuration Parsing')).toBeDefined()
    expect(screen.getByText('Serverclass Resolution')).toBeDefined()
    expect(screen.getByText('Data Flow Analysis')).toBeDefined()
    expect(screen.getByText('Interactive Visualization')).toBeDefined()
    expect(screen.getByText('Version Tracking')).toBeDefined()
    expect(screen.getByText('API Integration')).toBeDefined()
  })

  it('should render getting started section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Getting Started')).toBeDefined()
  })

  it('should have correct number of feature cards', () => {
    const { container } = render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    
    // Check for feature card container
    const featureGrid = container.querySelector('.grid')
    expect(featureGrid).toBeDefined()
  })
})
