/**
 * Tests for Card component.
 */

import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/preact'
import { Card } from './Card'

describe('Card', () => {
  it('should render children', () => {
    render(<Card>Card content</Card>)
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('should render with title', () => {
    render(<Card title="Card Title">Content</Card>)
    expect(screen.getByText('Card Title')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Card Title')
  })

  it('should render without title', () => {
    render(<Card>Content only</Card>)
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  it('should render with actions', () => {
    render(
      <Card title="Title" actions={<button>Action</button>}>
        Content
      </Card>
    )
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
  })

  it('should render header with actions only (no title)', () => {
    render(
      <Card actions={<button>Edit</button>}>
        Content
      </Card>
    )
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  it('should apply custom className', () => {
    const { container } = render(<Card class="custom-card">Content</Card>)
    expect(container.querySelector('.custom-card')).toBeInTheDocument()
  })

  it('should render complex children', () => {
    render(
      <Card title="Complex">
        <p>Paragraph 1</p>
        <p>Paragraph 2</p>
        <ul>
          <li>Item 1</li>
          <li>Item 2</li>
        </ul>
      </Card>
    )
    expect(screen.getByText('Paragraph 1')).toBeInTheDocument()
    expect(screen.getByText('Paragraph 2')).toBeInTheDocument()
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
  })
})
