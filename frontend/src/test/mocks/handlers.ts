/**
 * MSW request handlers for API mocking.
 *
 * These handlers intercept API requests during tests and return mock responses.
 */

import { http, HttpResponse } from 'msw'

// Mock data
export const mockSystemStatus = {
  success: true,
  data: {
    running: true,
    last_update: '2024-01-15T10:30:00Z',
    next_scheduled: '2024-01-15T11:00:00Z',
    orchestrator: { status: 'running' },
    display_state: {
      current_image_id: 'img_123',
      last_refresh: '2024-01-15T10:30:00Z',
    },
  },
}

export const mockSystemInfo = {
  success: true,
  data: {
    cpu_percent: 25.5,
    memory_percent: 45.2,
    disk_percent: 60.0,
    temperature: 42.5,
    uptime: '5 days, 3:24:15',
    platform: 'Linux',
  },
}

export const mockSchedulerStatus = {
  success: true,
  data: {
    paused: false,
    next_update: '2024-01-15T11:00:00Z',
    last_update: '2024-01-15T10:00:00Z',
    current_time: '2024-01-15T10:30:00Z',
    timezone: 'UTC',
    update_time: '09:00',
  },
}

export const mockDisplayCurrent = {
  success: true,
  data: {
    image_id: 'img_123',
    last_update: '2024-01-15T10:30:00Z',
    plugin_name: 'Clock',
    instance_name: 'Main Clock',
    has_preview: true,
    display_count: 42,
  },
}

export const mockPlugins = {
  success: true,
  data: [
    {
      id: 'clock',
      display_name: 'Clock',
      class_name: 'ClockPlugin',
      description: 'Display a clock',
      author: 'Artframe',
      version: '1.0.0',
      icon: '🕐',
    },
    {
      id: 'quote',
      display_name: 'Quote of the Day',
      class_name: 'QuotePlugin',
      description: 'Display inspirational quotes',
      author: 'Artframe',
      version: '1.0.0',
      icon: '💬',
    },
  ],
}

export const mockInstances = {
  success: true,
  data: [
    {
      id: 'inst_1',
      plugin_id: 'clock',
      name: 'Main Clock',
      settings: { show_seconds: true },
      enabled: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
  ],
}

export const mockSchedules = {
  success: true,
  slots: {
    '0-9': {
      day: 0,
      hour: 9,
      key: '0-9',
      target_type: 'instance',
      target_id: 'inst_1',
      target_name: 'Main Clock',
    },
  },
  slot_count: 1,
}

export const mockConnections = {
  success: true,
  data: {
    display: true,
    storage: true,
  },
}

export const mockConfig = {
  success: true,
  data: {
    display: {
      driver: 'mock',
      update_time: '09:00',
    },
    storage: {
      data_dir: '/tmp/artframe',
    },
  },
}

// Request handlers
export const handlers = [
  // System routes
  http.get('/api/system/status', () => {
    return HttpResponse.json(mockSystemStatus)
  }),

  http.get('/api/system/info', () => {
    return HttpResponse.json(mockSystemInfo)
  }),

  http.get('/api/system/connections', () => {
    return HttpResponse.json(mockConnections)
  }),

  http.get('/api/system/logs', () => {
    return HttpResponse.json({
      success: true,
      data: [
        { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'System started' },
      ],
    })
  }),

  // Scheduler routes
  http.get('/api/scheduler/status', () => {
    return HttpResponse.json(mockSchedulerStatus)
  }),

  http.post('/api/scheduler/pause', () => {
    return HttpResponse.json({ success: true, message: 'Scheduler paused' })
  }),

  http.post('/api/scheduler/resume', () => {
    return HttpResponse.json({ success: true, message: 'Scheduler resumed' })
  }),

  // Display routes
  http.get('/api/display/current', () => {
    return HttpResponse.json(mockDisplayCurrent)
  }),

  http.get('/api/display/health', () => {
    return HttpResponse.json({
      success: true,
      data: { refresh_count: 42, last_refresh: '2024-01-15T10:30:00Z' },
    })
  }),

  http.post('/api/display/refresh', () => {
    return HttpResponse.json({ success: true, message: 'Display refreshed' })
  }),

  http.post('/api/display/clear', () => {
    return HttpResponse.json({ success: true, message: 'Display cleared' })
  }),

  // Plugin routes
  http.get('/api/plugins', () => {
    return HttpResponse.json(mockPlugins)
  }),

  http.get('/api/plugins/:id', ({ params }) => {
    const plugin = mockPlugins.data.find(p => p.id === params.id)
    if (plugin) {
      return HttpResponse.json({ success: true, data: plugin })
    }
    return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
  }),

  // Instance routes
  http.get('/api/instances', () => {
    return HttpResponse.json(mockInstances)
  }),

  http.get('/api/instances/:id', ({ params }) => {
    const instance = mockInstances.data.find(i => i.id === params.id)
    if (instance) {
      return HttpResponse.json({ success: true, data: instance })
    }
    return HttpResponse.json({ detail: 'Instance not found' }, { status: 404 })
  }),

  http.post('/api/instances', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({
      success: true,
      data: {
        id: 'inst_new',
        ...body,
        enabled: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    })
  }),

  http.delete('/api/instances/:id', () => {
    return HttpResponse.json({ success: true, message: 'Instance deleted' })
  }),

  // Schedule routes
  http.get('/api/schedules', () => {
    return HttpResponse.json(mockSchedules)
  }),

  http.get('/api/schedules/current', () => {
    return HttpResponse.json({
      success: true,
      data: {
        has_content: true,
        source_type: 'schedule',
        target_type: 'instance',
        target_id: 'inst_1',
        target_name: 'Main Clock',
      },
    })
  }),

  http.post('/api/schedules/slot', () => {
    return HttpResponse.json({ success: true, message: 'Slot set' })
  }),

  http.delete('/api/schedules/slot', () => {
    return HttpResponse.json({ success: true, message: 'Slot cleared' })
  }),

  // Config routes
  http.get('/api/config', () => {
    return HttpResponse.json(mockConfig)
  }),

  http.put('/api/config', () => {
    return HttpResponse.json({ success: true, message: 'Config updated' })
  }),
]
