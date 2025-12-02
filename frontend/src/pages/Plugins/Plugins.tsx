import { useState } from 'preact/hooks'
import clsx from 'clsx'
import { Card, Button, showToast, SettingsForm } from '@/components'
import {
  usePlugins,
  useInstances,
  useCreateInstance,
  useUpdateInstance,
  useDeleteInstance,
  useToggleInstance,
  useTestInstance,
} from '@/queries'
import type { Plugin, PluginInstance } from '@/api/types'

export const Plugins = () => {
  const { data: plugins = [], isLoading: pluginsLoading } = usePlugins()
  const { data: instances = [], isLoading: instancesLoading } = useInstances()

  const [modalOpen, setModalOpen] = useState(false)
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null)
  const [editingInstance, setEditingInstance] = useState<PluginInstance | null>(null)

  const openCreateModal = (plugin: Plugin) => {
    setSelectedPlugin(plugin)
    setEditingInstance(null)
    setModalOpen(true)
  }

  const openEditModal = (instance: PluginInstance) => {
    const plugin = plugins.find((p) => p.id === instance.plugin_id)
    if (plugin) {
      setSelectedPlugin(plugin)
      setEditingInstance(instance)
      setModalOpen(true)
    }
  }

  const closeModal = () => {
    setModalOpen(false)
    setSelectedPlugin(null)
    setEditingInstance(null)
  }

  return (
    <div class="max-w-7xl mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Available Plugins */}
        <Card title="Available Plugins">
          {pluginsLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading plugins...</p>
          ) : plugins.length === 0 ? (
            <div class="text-center py-12 text-gray-500">
              <h3 class="text-lg font-semibold text-gray-600 mb-2">No plugins found</h3>
              <p>No plugins are currently installed.</p>
            </div>
          ) : (
            <div class="flex flex-col gap-4 mt-5">
              {plugins.map((plugin) => (
                <div key={plugin.id} class="border border-gray-200 rounded-lg p-5 bg-white transition-all hover:shadow-lg hover:-translate-y-0.5">
                  <h3 class="font-semibold text-gray-800 mb-2">{plugin.display_name}</h3>
                  <div class="text-xs text-gray-500 mb-2">
                    {plugin.author} • v{plugin.version}
                  </div>
                  <div class="text-gray-600 mb-4 leading-relaxed">
                    {plugin.description || 'No description available'}
                  </div>
                  <Button size="small" onClick={() => openCreateModal(plugin)}>
                    + Create Instance
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Instances */}
        <Card title="Plugin Instances">
          {instancesLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading instances...</p>
          ) : instances.length === 0 ? (
            <div class="text-center py-12 text-gray-500">
              <h3 class="text-lg font-semibold text-gray-600 mb-2">No instances yet</h3>
              <p>Create a plugin instance from the Available Plugins panel to get started.</p>
            </div>
          ) : (
            <div class="flex flex-col gap-3 mt-5">
              {instances.map((instance) => (
                <InstanceItem
                  key={instance.id}
                  instance={instance}
                  plugins={plugins}
                  onEdit={() => openEditModal(instance)}
                />
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Instance Modal */}
      {modalOpen && selectedPlugin && (
        <InstanceModal
          plugin={selectedPlugin}
          instance={editingInstance}
          onClose={closeModal}
        />
      )}
    </div>
  )
}

interface InstanceItemProps {
  instance: PluginInstance
  plugins: Plugin[]
  onEdit: () => void
}

const InstanceItem = ({ instance, plugins, onEdit }: InstanceItemProps) => {
  const plugin = plugins.find((p) => p.id === instance.plugin_id)
  const pluginName = plugin?.display_name || instance.plugin_id

  const deleteInstance = useDeleteInstance()
  const toggleInstance = useToggleInstance()
  const testInstance = useTestInstance()

  const handleToggle = async () => {
    try {
      await toggleInstance.mutateAsync({ id: instance.id, enable: !instance.enabled })
      showToast(
        `Instance ${instance.enabled ? 'disabled' : 'enabled'} successfully`,
        'success'
      )
    } catch {
      showToast('Failed to toggle instance', 'error')
    }
  }

  const handleTest = async () => {
    showToast('Testing instance...', 'info')
    try {
      await testInstance.mutateAsync(instance.id)
      showToast('Test successful!', 'success')
    } catch (err) {
      showToast(`Test failed: ${(err as Error).message}`, 'error')
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${instance.name}"?`)) return
    try {
      await deleteInstance.mutateAsync(instance.id)
      showToast('Instance deleted successfully', 'success')
    } catch {
      showToast('Failed to delete instance', 'error')
    }
  }

  return (
    <div class="border border-gray-200 rounded-lg p-4 bg-white transition-all hover:shadow-md">
      <div class="flex justify-between items-start mb-2">
        <h4 class="font-semibold text-gray-800">{instance.name}</h4>
        <span class={clsx('status-badge', instance.enabled ? 'enabled' : 'disabled')}>
          {instance.enabled ? 'Enabled' : 'Disabled'}
        </span>
      </div>
      <div class="text-sm text-gray-500 mb-3">{pluginName}</div>
      <div class="flex flex-wrap gap-2">
        <Button size="small" variant="secondary" onClick={onEdit}>
          Edit
        </Button>
        <Button
          size="small"
          variant={instance.enabled ? 'warning' : 'primary'}
          onClick={handleToggle}
          loading={toggleInstance.isPending}
        >
          {instance.enabled ? 'Disable' : 'Enable'}
        </Button>
        <Button
          size="small"
          variant="secondary"
          onClick={handleTest}
          loading={testInstance.isPending}
        >
          Test
        </Button>
        <Button
          size="small"
          variant="danger"
          onClick={handleDelete}
          loading={deleteInstance.isPending}
        >
          Delete
        </Button>
      </div>
    </div>
  )
}

interface InstanceModalProps {
  plugin: Plugin
  instance: PluginInstance | null
  onClose: () => void
}

const InstanceModal = ({ plugin, instance, onClose }: InstanceModalProps) => {
  const [name, setName] = useState(instance?.name || '')
  const [settings, setSettings] = useState<Record<string, unknown>>(instance?.settings || {})

  const createInstance = useCreateInstance()
  const updateInstance = useUpdateInstance()

  const handleSettingsChange = (key: string, value: unknown) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: Event) => {
    e.preventDefault()

    try {
      if (instance) {
        await updateInstance.mutateAsync({
          id: instance.id,
          data: { name, settings },
        })
        showToast('Instance updated successfully', 'success')
      } else {
        await createInstance.mutateAsync({
          plugin_id: plugin.id,
          name,
          settings,
        })
        showToast('Instance created successfully', 'success')
      }
      onClose()
    } catch (err) {
      showToast(`Failed to save instance: ${(err as Error).message}`, 'error')
    }
  }

  return (
    <div class="modal-overlay" onClick={(e) => {
      if ((e.target as HTMLElement).classList.contains('modal-overlay')) onClose()
    }}>
      <div class="modal">
        <div class="flex justify-between items-center p-5 border-b border-gray-200">
          <h3 class="text-lg font-semibold">{instance ? `Edit ${instance.name}` : `Create ${plugin.display_name} Instance`}</h3>
          <button class="text-3xl text-gray-400 hover:text-gray-600 leading-none" onClick={onClose}>&times;</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div class="p-5 max-h-[70vh] overflow-y-auto">
            <div class="mb-5">
              <label class="block mb-1 font-medium text-gray-700" for="instance_name">Instance Name</label>
              <input
                type="text"
                id="instance_name"
                name="instance_name"
                class="input"
                value={name}
                onInput={(e) => setName((e.target as HTMLInputElement).value)}
                required
              />
            </div>

            {plugin.settings_schema ? (
              <SettingsForm
                schema={plugin.settings_schema}
                values={settings}
                onChange={handleSettingsChange}
              />
            ) : (
              <p class="text-gray-500 italic">This plugin has no configurable settings.</p>
            )}
          </div>
          <div class="flex gap-3 justify-end p-5 border-t border-gray-200">
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={createInstance.isPending || updateInstance.isPending}
            >
              {instance ? 'Save Changes' : 'Create Instance'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
