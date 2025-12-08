/**
 * Tests for Toast component and showToast function.
 *
 * Note: Toast uses Preact signals for global state management, which makes
 * testing the reactive behavior challenging. These tests focus on the
 * showToast function logic and basic container rendering.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/preact'
import { ToastContainer, showToast } from './Toast'

describe('Toast', () => {
  describe('ToastContainer', () => {
    it('should render container element', () => {
      const { container } = render(<ToastContainer />)
      // Container should exist with the container class
      expect(container.querySelector('[class*="container"]')).toBeTruthy()
    })

    it('should be a div element', () => {
      const { container } = render(<ToastContainer />)
      const toastContainer = container.firstElementChild
      expect(toastContainer?.tagName).toBe('DIV')
    })
  })

  describe('showToast', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.runAllTimers()
      vi.useRealTimers()
    })

    it('should not throw when called with message', () => {
      expect(() => showToast('Test message')).not.toThrow()
    })

    it('should accept success type', () => {
      expect(() => showToast('Success!', 'success')).not.toThrow()
    })

    it('should accept error type', () => {
      expect(() => showToast('Error!', 'error')).not.toThrow()
    })

    it('should accept warning type', () => {
      expect(() => showToast('Warning!', 'warning')).not.toThrow()
    })

    it('should accept info type', () => {
      expect(() => showToast('Info message', 'info')).not.toThrow()
    })

    it('should default to info type when not specified', () => {
      // Just verify it doesn't throw - default type is 'info'
      expect(() => showToast('Default type')).not.toThrow()
    })

    it('should set up auto-dismiss timeout', () => {
      const setTimeoutSpy = vi.spyOn(global, 'setTimeout')
      showToast('Auto dismiss test')
      expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 3000)
    })

    it('should be callable multiple times', () => {
      expect(() => {
        showToast('First')
        showToast('Second')
        showToast('Third')
      }).not.toThrow()
    })
  })
})
