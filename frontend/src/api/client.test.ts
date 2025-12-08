/**
 * Tests for API client utilities.
 */

import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../test/mocks/server'
import { get, post, put, del, ApiError } from './client'

describe('API Client', () => {
  describe('get', () => {
    it('should make a GET request and return data', async () => {
      const data = await get('/system/info')
      expect(data).toEqual({
        cpu_percent: 25.5,
        memory_percent: 45.2,
        disk_percent: 60.0,
        temperature: 42.5,
        uptime: '5 days, 3:24:15',
        platform: 'Linux',
      })
    })

    it('should throw ApiError on failed response', async () => {
      server.use(
        http.get('/api/test/error', () => {
          return HttpResponse.json(
            { success: false, error: 'Something went wrong' },
            { status: 400 }
          )
        })
      )

      await expect(get('/test/error')).rejects.toThrow(ApiError)
    })

    it('should include error message in ApiError', async () => {
      server.use(
        http.get('/api/test/error-msg', () => {
          return HttpResponse.json(
            { success: false, error: 'Custom error message' },
            { status: 500 }
          )
        })
      )

      try {
        await get('/test/error-msg')
        expect.fail('Should have thrown')
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect((error as ApiError).message).toBe('Custom error message')
        expect((error as ApiError).status).toBe(500)
      }
    })
  })

  describe('post', () => {
    it('should make a POST request with data', async () => {
      server.use(
        http.post('/api/test/create', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>
          return HttpResponse.json({
            success: true,
            data: { id: 'new_item', ...body },
          })
        })
      )

      const result = await post('/test/create', { name: 'Test Item' })
      expect(result).toEqual({ id: 'new_item', name: 'Test Item' })
    })

    it('should make a POST request without data', async () => {
      server.use(
        http.post('/api/test/action', () => {
          return HttpResponse.json({
            success: true,
            data: { status: 'completed' },
          })
        })
      )

      const result = await post('/test/action')
      expect(result).toEqual({ status: 'completed' })
    })

    it('should trigger display refresh', async () => {
      const result = await post('/display/refresh')
      // MSW handler returns success
      expect(result).toBeUndefined() // data is undefined in mock
    })
  })

  describe('put', () => {
    it('should make a PUT request with data', async () => {
      server.use(
        http.put('/api/test/update', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>
          return HttpResponse.json({
            success: true,
            data: { updated: true, ...body },
          })
        })
      )

      const result = await put('/test/update', { name: 'Updated' })
      expect(result).toEqual({ updated: true, name: 'Updated' })
    })

    it('should update config', async () => {
      const result = await put('/config', { display: { update_time: '10:00' } })
      // MSW handler returns success
      expect(result).toBeUndefined()
    })
  })

  describe('del', () => {
    it('should make a DELETE request', async () => {
      server.use(
        http.delete('/api/test/item/123', () => {
          return HttpResponse.json({
            success: true,
            data: { deleted: true },
          })
        })
      )

      const result = await del('/test/item/123')
      expect(result).toEqual({ deleted: true })
    })

    it('should make a DELETE request with body', async () => {
      server.use(
        http.delete('/api/test/bulk-delete', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>
          return HttpResponse.json({
            success: true,
            data: { deleted_count: (body.ids as string[]).length },
          })
        })
      )

      const result = await del('/test/bulk-delete', { ids: ['1', '2', '3'] })
      expect(result).toEqual({ deleted_count: 3 })
    })

    it('should delete an instance', async () => {
      const result = await del('/instances/inst_1')
      // MSW handler returns success
      expect(result).toBeUndefined()
    })
  })

  describe('ApiError', () => {
    it('should have correct name property', () => {
      const error = new ApiError('Test error', 404)
      expect(error.name).toBe('ApiError')
    })

    it('should store status code', () => {
      const error = new ApiError('Not found', 404)
      expect(error.status).toBe(404)
    })

    it('should work without status', () => {
      const error = new ApiError('Unknown error')
      expect(error.message).toBe('Unknown error')
      expect(error.status).toBeUndefined()
    })
  })
})
