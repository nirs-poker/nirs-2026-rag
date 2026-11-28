import type { AskRequest, AskResponse, AskSource } from './contracts'

function isAskSource(value: unknown): value is AskSource {
  return typeof value === 'object' && value !== null
    && 'id' in value && typeof value.id === 'string'
    && 'title' in value && typeof value.title === 'string'
    && 'text' in value && typeof value.text === 'string'
}

function isStyle(value: unknown): boolean {
  if (typeof value !== 'object' || value === null) return false
  return 'prefix' in value && typeof value.prefix === 'string' && Array.from(value.prefix).length <= 32
    && 'verbosity' in value && ['normal', 'brief', 'detailed'].includes(String(value.verbosity))
    && 'simple' in value && typeof value.simple === 'boolean'
}

function isAskResponse(value: unknown): value is AskResponse {
  return typeof value === 'object' && value !== null
    && 'status' in value && (value.status === 'ok' || value.status === 'no_sources' || value.status === 'style_updated')
    && 'answer' in value && typeof value.answer === 'string' && value.answer.trim().length > 0
    && 'sources' in value && Array.isArray(value.sources) && value.sources.every(isAskSource)
    && (!('style' in value) || isStyle(value.style))
}

export const api = {
  async ask(payload: AskRequest, signal: AbortSignal): Promise<AskResponse> {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })
    if (!response.ok) {
      if (response.status === 502) {
        throw new Error('Сервер не получил ответ от модели. Повтори запрос.')
      }
      if (response.status === 500 || response.status === 503 || response.status === 504) {
        throw new Error('Сервер тренера недоступен. Проверь, запущен ли Python-сервер.')
      }
      throw new Error('Сервер тренера отклонил запрос.')
    }
    const data: unknown = await response.json()
    if (!isAskResponse(data)) throw new Error('Получен ответ в неожиданном формате.')
    return data
  },
}
