import type { AskSource, StylePreferences } from '../api/contracts'

export const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'] as const
export const suits = { s: '♠', h: '♥', d: '♦', c: '♣' } as const
export const positions = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'] as const

export type Suit = keyof typeof suits
export type Card = `${typeof ranks[number]}${Suit}`

export interface Message {
  id: string
  role: 'user' | 'bot'
  text: string
  heading?: string
  sources?: AskSource[]
  afterHandId?: string
}

export interface HandStep {
  label: string
  quality?: 'opponent' | 'good' | 'miss'
  board: Card[]
  pot: number | null
  hero: string
  opponent: string
}

export interface Hand {
  id: string
  cards: [Card, Card]
  heroPosition: string
  opponentPosition: string
  steps: HandStep[]
  stepIndex: number
  open: boolean
  unread?: number
  setup?: { heroStack: number; opponentStack: number; ante: number; actions?: string }
  messages: Message[]
}

export interface Chat {
  id: string
  title: string
  draft: string
  style?: StylePreferences
  messages: Message[]
  hands: Hand[]
  selectedHandId: string | null
}

export interface Workspace {
  chats: Chat[]
  activeChatId: string | null
}

export const formatBB = (value: number) => `${value.toLocaleString('ru-RU')} ББ`
export const cardLabel = (card: Card) => `${card[0]}${suits[card[1] as Suit]}`

