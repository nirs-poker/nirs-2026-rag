import { api } from '../api'
import type { Message } from './chatTypes'

export function questionError(question: string): string | undefined {
  if (Array.from(question).length > 1500) {
    return 'Вопрос должен быть не длиннее 1500 символов.'
  }
}

export async function requestTrainerReply(question: string, signal: AbortSignal): Promise<Message> {
  const reply = await api.ask({ question }, signal)
  return { id: crypto.randomUUID(), role: 'bot', text: reply.answer, sources: reply.sources }
}
