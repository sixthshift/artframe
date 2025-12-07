import type { SettingsSchema, SettingsField, SettingsSection, components } from '@/api/types'

// Field from API may have slightly different shape (null vs undefined)
type ApiSettingsField = {
  type: string
  label: string
  description?: string | null
  required?: boolean
  default?: unknown
  options?: Array<{ [key: string]: string }> | null
  min?: number | null
  max?: number | null
  placeholder?: string | null
}

// API-generated schema type (sections is optional)
type ApiSettingsSchema = components['schemas']['SettingsSchema']

// Schema can be either sections-based or flat dict from API
type SchemaInput = SettingsSchema | ApiSettingsSchema | { [key: string]: ApiSettingsField }

interface SettingsFormProps {
  schema: SchemaInput
  values: Record<string, unknown>
  onChange: (key: string, value: unknown) => void
}

// Convert API field to internal SettingsField format
function normalizeField(key: string, field: ApiSettingsField): SettingsField {
  return {
    key,
    type: field.type,
    label: field.label,
    description: field.description ?? undefined,
    help: field.description ?? undefined,
    required: field.required,
    default: field.default,
    min: field.min ?? undefined,
    max: field.max ?? undefined,
    placeholder: field.placeholder ?? undefined,
    options: field.options?.map(opt => ({
      value: opt.value || Object.keys(opt)[0] || '',
      label: opt.label || Object.values(opt)[0] || '',
    })),
  }
}

// Convert flat dict schema to sections format
function normalizeSchema(schema: SchemaInput): SettingsSection[] {
  // If it already has sections, use them (normalize fields which may be optional from API)
  if ('sections' in schema && Array.isArray(schema.sections)) {
    return schema.sections.map(section => ({
      title: section.title,
      fields: (section.fields ?? []).map(field => ({
        key: field.key,
        type: field.type,
        label: field.label,
        description: field.description ?? undefined,
        help: field.help ?? field.description ?? undefined,
        required: field.required,
        default: field.default ?? undefined,
        min: field.min ?? undefined,
        max: field.max ?? undefined,
        placeholder: field.placeholder ?? undefined,
        options: field.options?.map(opt => ({
          value: String(opt.value ?? Object.keys(opt)[0] ?? ''),
          label: String(opt.label ?? Object.values(opt)[0] ?? ''),
        })),
      }))
    }))
  }

  // Convert flat dict to a single section
  const fields: SettingsField[] = Object.entries(schema).map(([key, field]) =>
    normalizeField(key, field)
  )

  return [{ title: 'Settings', fields }]
}

export const SettingsForm = ({ schema, values, onChange }: SettingsFormProps) => {
  const sections = normalizeSchema(schema)

  const shouldShowField = (field: SettingsField): boolean => {
    if (!field.showWhen) return true
    return values[field.showWhen.key] === field.showWhen.value
  }

  const renderField = (field: SettingsField) => {
    if (!shouldShowField(field)) return null

    const value = values[field.key] ?? field.default ?? ''

    switch (field.type) {
      case 'boolean':
        return (
          <div key={field.key} class="form-group">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={Boolean(value)}
                onChange={(e) => onChange(field.key, (e.target as HTMLInputElement).checked)}
                class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span class="font-medium text-gray-700">{field.label}</span>
            </label>
            {field.help && <p class="text-sm text-gray-500 mt-1 ml-6">{field.help}</p>}
          </div>
        )

      case 'select':
        return (
          <div key={field.key} class="form-group">
            <label class="block mb-1 font-medium text-gray-700">{field.label}</label>
            <select
              class="select"
              value={String(value)}
              onChange={(e) => onChange(field.key, (e.target as HTMLSelectElement).value)}
              required={field.required}
            >
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {field.help && <p class="text-sm text-gray-500 mt-1">{field.help}</p>}
          </div>
        )

      case 'number':
        return (
          <div key={field.key} class="form-group">
            <label class="block mb-1 font-medium text-gray-700">{field.label}</label>
            <input
              type="number"
              class="input"
              value={value as number}
              min={field.min}
              max={field.max}
              placeholder={field.placeholder}
              required={field.required}
              onChange={(e) => onChange(field.key, Number((e.target as HTMLInputElement).value))}
            />
            {field.help && <p class="text-sm text-gray-500 mt-1">{field.help}</p>}
          </div>
        )

      case 'color':
        return (
          <div key={field.key} class="form-group">
            <label class="block mb-1 font-medium text-gray-700">{field.label}</label>
            <div class="flex items-center gap-2">
              <input
                type="color"
                class="w-10 h-10 p-0 border border-gray-300 rounded cursor-pointer"
                value={String(value)}
                onChange={(e) => onChange(field.key, (e.target as HTMLInputElement).value)}
              />
              <input
                type="text"
                class="input flex-1"
                value={String(value)}
                placeholder={field.placeholder || '#000000'}
                onChange={(e) => onChange(field.key, (e.target as HTMLInputElement).value)}
              />
            </div>
            {field.help && <p class="text-sm text-gray-500 mt-1">{field.help}</p>}
          </div>
        )

      case 'password':
        return (
          <div key={field.key} class="form-group">
            <label class="block mb-1 font-medium text-gray-700">{field.label}</label>
            <input
              type="password"
              class="input"
              value={String(value)}
              placeholder={field.placeholder}
              required={field.required}
              onChange={(e) => onChange(field.key, (e.target as HTMLInputElement).value)}
            />
            {field.help && <p class="text-sm text-gray-500 mt-1">{field.help}</p>}
          </div>
        )

      case 'url':
        return (
          <div key={field.key} class="form-group">
            <label class="block mb-1 font-medium text-gray-700">{field.label}</label>
            <input
              type="url"
              class="input"
              value={String(value)}
              placeholder={field.placeholder}
              required={field.required}
              onChange={(e) => onChange(field.key, (e.target as HTMLInputElement).value)}
            />
            {field.help && <p class="text-sm text-gray-500 mt-1">{field.help}</p>}
          </div>
        )

      case 'string':
      default:
        return (
          <div key={field.key} class="form-group">
            <label class="block mb-1 font-medium text-gray-700">{field.label}</label>
            <input
              type="text"
              class="input"
              value={String(value)}
              placeholder={field.placeholder}
              required={field.required}
              onChange={(e) => onChange(field.key, (e.target as HTMLInputElement).value)}
            />
            {field.help && <p class="text-sm text-gray-500 mt-1">{field.help}</p>}
          </div>
        )
    }
  }

  return (
    <div class="settings-form space-y-6">
      {sections.map((section) => (
        <div key={section.title} class="settings-section">
          <h4 class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3 pb-2 border-b border-gray-200">
            {section.title}
          </h4>
          <div class="space-y-4">
            {section.fields.map((field) => renderField(field))}
          </div>
        </div>
      ))}
    </div>
  )
}
