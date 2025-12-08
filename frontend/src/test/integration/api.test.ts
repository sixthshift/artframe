/**
 * Integration tests for API layer with MSW.
 *
 * Tests that the API client correctly integrates with the mock server.
 * Note: The client adds /api prefix and extracts the data field from responses.
 */

import { describe, expect, it } from 'vitest'
import { get, post, put, del, ApiError } from '@/api/client'

describe('API Integration', () => {
  describe('System API', () => {
    it('should fetch system status', async () => {
      const result = await get('/system/status')
      expect(result).toHaveProperty('running', true)
      expect(result).toHaveProperty('last_update')
    })

    it('should fetch system info', async () => {
      const result = await get('/system/info')
      expect(result).toHaveProperty('cpu_percent')
      expect(result).toHaveProperty('memory_percent')
      expect(result).toHaveProperty('platform')
    })

    it('should fetch connections', async () => {
      const result = await get('/system/connections')
      expect(result).toHaveProperty('display')
      expect(result).toHaveProperty('storage')
    })

    it('should fetch logs', async () => {
      const result = await get<Array<{ timestamp: string; level: string; message: string }>>('/system/logs')
      expect(result).toBeInstanceOf(Array)
      expect(result.length).toBeGreaterThan(0)
    })
  })

  describe('Scheduler API', () => {
    it('should fetch scheduler status', async () => {
      const result = await get('/scheduler/status')
      expect(result).toHaveProperty('paused')
      expect(result).toHaveProperty('next_update')
      expect(result).toHaveProperty('current_time')
    })

    it('should pause scheduler', async () => {
      // POST returns undefined when no data field in response
      const result = await post('/scheduler/pause')
      expect(result).toBeUndefined()
    })

    it('should resume scheduler', async () => {
      const result = await post('/scheduler/resume')
      expect(result).toBeUndefined()
    })
  })

  describe('Display API', () => {
    it('should fetch current display', async () => {
      const result = await get('/display/current')
      expect(result).toHaveProperty('image_id')
      expect(result).toHaveProperty('plugin_name')
      expect(result).toHaveProperty('has_preview')
    })

    it('should fetch display health', async () => {
      const result = await get('/display/health')
      expect(result).toHaveProperty('refresh_count')
      expect(result).toHaveProperty('last_refresh')
    })

    it('should trigger display refresh', async () => {
      const result = await post('/display/refresh')
      expect(result).toBeUndefined()
    })

    it('should clear display', async () => {
      const result = await post('/display/clear')
      expect(result).toBeUndefined()
    })
  })

  describe('Plugins API', () => {
    it('should fetch plugins list', async () => {
      const result = await get<Array<{ id: string; display_name: string }>>('/plugins')
      expect(result).toBeInstanceOf(Array)
      expect(result.length).toBe(2)
      expect(result[0]).toHaveProperty('id', 'clock')
    })

    it('should fetch a single plugin', async () => {
      const result = await get('/plugins/clock')
      expect(result).toHaveProperty('id', 'clock')
      expect(result).toHaveProperty('display_name', 'Clock')
    })

    it('should return 404 for unknown plugin', async () => {
      try {
        await get('/plugins/unknown')
        expect.fail('Should have thrown')
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect((error as ApiError).status).toBe(404)
      }
    })
  })

  describe('Instances API', () => {
    it('should fetch instances list', async () => {
      const result = await get<Array<{ id: string; plugin_id: string }>>('/instances')
      expect(result).toBeInstanceOf(Array)
      expect(result.length).toBe(1)
      expect(result[0]).toHaveProperty('id', 'inst_1')
    })

    it('should create an instance', async () => {
      const newInstance = {
        plugin_id: 'clock',
        name: 'New Clock',
        settings: { show_seconds: false },
      }
      const result = await post('/instances', newInstance)
      expect(result).toHaveProperty('id', 'inst_new')
      expect(result).toHaveProperty('plugin_id', 'clock')
    })

    it('should delete an instance', async () => {
      const result = await del('/instances/inst_1')
      expect(result).toBeUndefined()
    })
  })

  describe('Schedules API', () => {
    it('should fetch schedules', async () => {
      // Schedules response has a different structure (not wrapped in data)
      const result = await get('/schedules')
      // The result might be undefined since there's no data field
      expect(result).toBeUndefined()
    })

    it('should fetch current schedule slot', async () => {
      const result = await get('/schedules/current')
      expect(result).toHaveProperty('has_content')
      expect(result).toHaveProperty('source_type')
    })

    it('should set a schedule slot', async () => {
      const result = await post('/schedules/slot', {
        day: 0,
        hour: 10,
        target_type: 'instance',
        target_id: 'inst_1',
      })
      expect(result).toBeUndefined()
    })

    it('should clear a schedule slot', async () => {
      const result = await del('/schedules/slot?day=0&hour=10')
      expect(result).toBeUndefined()
    })
  })

  describe('Config API', () => {
    it('should fetch config', async () => {
      const result = await get('/config')
      expect(result).toHaveProperty('display')
      expect(result).toHaveProperty('storage')
    })

    it('should update config', async () => {
      const result = await put('/config', { display: { driver: 'mock' } })
      expect(result).toBeUndefined()
    })
  })
})
