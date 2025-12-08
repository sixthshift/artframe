/**
 * Tests for system and display query keys.
 *
 * Note: Testing React Query hooks with Preact requires additional setup
 * due to the React/Preact compat layer. These tests focus on the query
 * key generators which are pure functions.
 */

import { describe, expect, it } from 'vitest'
import { systemKeys, displayKeys } from './useSystem'

describe('Query Keys', () => {
  describe('systemKeys', () => {
    it('should generate all key', () => {
      expect(systemKeys.all).toEqual(['system'])
    })

    it('should generate status key', () => {
      expect(systemKeys.status()).toEqual(['system', 'status'])
    })

    it('should generate info key', () => {
      expect(systemKeys.info()).toEqual(['system', 'info'])
    })

    it('should generate connections key', () => {
      expect(systemKeys.connections()).toEqual(['system', 'connections'])
    })

    it('should generate scheduler key', () => {
      expect(systemKeys.scheduler()).toEqual(['system', 'scheduler'])
    })

    it('should generate logs key without level', () => {
      expect(systemKeys.logs()).toEqual(['system', 'logs', undefined])
    })

    it('should generate logs key with level', () => {
      expect(systemKeys.logs('ERROR')).toEqual(['system', 'logs', 'ERROR'])
    })

    it('should generate logs key with different levels', () => {
      expect(systemKeys.logs('INFO')).toEqual(['system', 'logs', 'INFO'])
      expect(systemKeys.logs('WARNING')).toEqual(['system', 'logs', 'WARNING'])
      expect(systemKeys.logs('DEBUG')).toEqual(['system', 'logs', 'DEBUG'])
    })

    it('should generate config key', () => {
      expect(systemKeys.config()).toEqual(['system', 'config'])
    })

    it('should have unique keys for different resources', () => {
      const status = systemKeys.status()
      const info = systemKeys.info()
      const connections = systemKeys.connections()

      expect(status).not.toEqual(info)
      expect(status).not.toEqual(connections)
      expect(info).not.toEqual(connections)
    })

    it('should include base key in all derived keys', () => {
      expect(systemKeys.status()[0]).toBe('system')
      expect(systemKeys.info()[0]).toBe('system')
      expect(systemKeys.connections()[0]).toBe('system')
      expect(systemKeys.scheduler()[0]).toBe('system')
      expect(systemKeys.logs()[0]).toBe('system')
      expect(systemKeys.config()[0]).toBe('system')
    })
  })

  describe('displayKeys', () => {
    it('should generate all key', () => {
      expect(displayKeys.all).toEqual(['display'])
    })

    it('should generate current key', () => {
      expect(displayKeys.current()).toEqual(['display', 'current'])
    })

    it('should generate health key', () => {
      expect(displayKeys.health()).toEqual(['display', 'health'])
    })

    it('should have unique keys for different resources', () => {
      const current = displayKeys.current()
      const health = displayKeys.health()

      expect(current).not.toEqual(health)
    })

    it('should include base key in all derived keys', () => {
      expect(displayKeys.current()[0]).toBe('display')
      expect(displayKeys.health()[0]).toBe('display')
    })

    it('should not overlap with system keys', () => {
      expect(displayKeys.all[0]).not.toBe(systemKeys.all[0])
    })
  })

  describe('Key immutability', () => {
    it('systemKeys.all should return consistent value', () => {
      const first = systemKeys.all
      const second = systemKeys.all
      expect(first).toBe(second)
    })

    it('displayKeys.all should return consistent value', () => {
      const first = displayKeys.all
      const second = displayKeys.all
      expect(first).toBe(second)
    })

    it('factory functions should return new arrays', () => {
      const first = systemKeys.status()
      const second = systemKeys.status()
      expect(first).not.toBe(second)
      expect(first).toEqual(second)
    })
  })
})
