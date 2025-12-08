/**
 * Tests for Button component.
 */

import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/preact'
import { Button } from './Button'

describe('Button', () => {
  it('should render children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('should be a button element by default', () => {
    render(<Button>Test</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('type', 'button')
  })

  it('should support submit type', () => {
    render(<Button type="submit">Submit</Button>)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'submit')
  })

  it('should support reset type', () => {
    render(<Button type="reset">Reset</Button>)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'reset')
  })

  it('should call onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('disabled')
  })

  it('should show loading state', () => {
    render(<Button loading>Normal Text</Button>)
    expect(screen.getByText('⏳ Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Normal Text')).not.toBeInTheDocument()
  })

  it('should be disabled when loading', () => {
    render(<Button loading>Loading</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('disabled')
  })

  it('should apply custom className', () => {
    render(<Button class="custom-class">Custom</Button>)
    expect(screen.getByRole('button')).toHaveClass('custom-class')
  })

  describe('variants', () => {
    it('should render primary variant by default', () => {
      render(<Button>Primary</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('primary')
    })

    it('should render secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>)
      expect(screen.getByRole('button')).toHaveClass('secondary')
    })

    it('should render warning variant', () => {
      render(<Button variant="warning">Warning</Button>)
      expect(screen.getByRole('button')).toHaveClass('warning')
    })

    it('should render danger variant', () => {
      render(<Button variant="danger">Danger</Button>)
      expect(screen.getByRole('button')).toHaveClass('danger')
    })

    it('should render success variant', () => {
      render(<Button variant="success">Success</Button>)
      expect(screen.getByRole('button')).toHaveClass('success')
    })
  })

  describe('sizes', () => {
    it('should render normal size by default', () => {
      render(<Button>Normal</Button>)
      const button = screen.getByRole('button')
      expect(button).not.toHaveClass('small')
    })

    it('should render small size', () => {
      render(<Button size="small">Small</Button>)
      expect(screen.getByRole('button')).toHaveClass('small')
    })
  })
})
