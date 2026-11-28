import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buildDialogueRequest } from '../src/modules/dialogue.ts'
import type { Chat } from '../src/modules/chatTypes.ts'

const chat: Chat = {
  id: 'one', title: '', draft: '', selectedHandId: 'a',
  style: { prefix: 'мяу', verbosity: 'brief', simple: true },
  messages: [{ id: '1', role: 'user', text: 'Общий вопрос' }],
  hands: ['a', 'b'].map(id => ({ id, cards: ['As', 'Kd'], heroPosition: 'BB', opponentPosition: 'BTN',
    steps: [], stepIndex: 0, open: true, messages: [{ id, role: 'bot', text: `Раздача ${id}` }] })),
}

test('history stays within selected thread, preferences stay within chat', () => {
  assert.equal(buildDialogueRequest('q', chat, null).history?.[0].content, 'Общий вопрос')
  assert.equal(buildDialogueRequest('q', chat, 'a').history?.[0].content, 'Раздача a')
  assert.equal(buildDialogueRequest('q', chat, 'b').history?.[0].content, 'Раздача b')
  assert.deepEqual(buildDialogueRequest('q', undefined, null).history, [])
  assert.equal(buildDialogueRequest('q', undefined, null).style, undefined)
  assert.deepEqual(buildDialogueRequest('q', chat, 'missing').history, [])
  assert.equal(buildDialogueRequest('q', chat, 'a').style?.prefix, 'мяу')
})

test('history has bounded size and omits current question', () => {
  const large = { ...chat, messages: Array.from({ length: 30 }, (_, id) => ({ id: String(id), role: 'user' as const, text: 'я'.repeat(2000) })) }
  const request = buildDialogueRequest('Текущий вопрос', large, null)
  assert.ok(request.history!.length <= 12)
  assert.ok(request.history!.reduce((n, m) => n + Array.from(m.content).length, 0) <= 8000)
  assert.ok(request.history!.every(m => Array.from(m.content).length <= 1500 && m.content !== request.question))
})

test('UTF-8 payload stays within API body limit', () => {
  const many = { ...chat, messages: Array.from({ length: 12 }, (_, id) => ({ id: String(id), role: 'user' as const, text: '🂡'.repeat(1500) })) }
  const request = buildDialogueRequest('🂡'.repeat(1500), many, null)
  assert.ok(new TextEncoder().encode(JSON.stringify(request)).length <= 32768)
})
