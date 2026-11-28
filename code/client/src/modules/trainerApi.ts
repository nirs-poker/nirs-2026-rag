import { api } from '../api'
import type { AskRequest, StylePreferences } from '../api/contracts'
import type { Message } from './chatTypes'

export function questionError(question: string): string | undefined {
  if (Array.from(question).length > 1500) {
    return 'Вопрос должен быть не длиннее 1500 символов.'
  }
}

export async function requestTrainerReply(payload: AskRequest, signal: AbortSignal): Promise<{ message: Message; style?: StylePreferences }> {
  const reply = await api.ask(payload, signal)
  return {
    message: { id: crypto.randomUUID(), role: 'bot', text: reply.answer, sources: reply.sources },
    style: reply.style,
  }
}
