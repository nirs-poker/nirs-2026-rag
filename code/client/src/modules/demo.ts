import type { Card, Workspace } from './chatTypes'
import { demoIntro, demoTitle, hand1Messages, hand2Messages } from './demoMessages'

export function demoWorkspace(): Workspace {
  const flop: Card[] = ['Kh', '7h', '2c']
  return {
    activeChatId: null,
    chats: [{
      id: 'demo',
      title: demoTitle,
      draft: '',
      selectedHandId: 'hand-2',
      messages: demoIntro,
      hands: [
        {
          id: 'hand-1', cards: ['As', 'Kd'], heroPosition: 'BB', opponentPosition: 'BTN',
          stepIndex: 3, open: false, unread: 1, messages: hand1Messages,
          steps: [
            { label: 'Рейз соперника на префлопе', quality: 'opponent', board: [], pot: 4, hero: '100 ББ', opponent: 'Рейз до 2,5 ББ' },
            { label: 'Колл на префлопе. Другое действие', quality: 'miss', board: [], pot: 5.5, hero: 'Колл', opponent: 'Рейз до 2,5 ББ' },
            { label: 'Чек на флопе. Нет оценки', board: flop, pot: 5.5, hero: 'Чек', opponent: '97,5 ББ' },
            { label: 'Ставка соперника на флопе', quality: 'opponent', board: flop, pot: 7.5, hero: 'Чек', opponent: 'Бет 2 ББ' },
          ],
        },
        {
          id: 'hand-2', cards: ['Qh', 'Jh'], heroPosition: 'BB', opponentPosition: 'BTN',
          stepIndex: 0, open: true, messages: hand2Messages,
          steps: [
            { label: 'Колл на префлопе. Совпадает с эталоном', quality: 'good', board: [], pot: 5.5, hero: 'Колл', opponent: 'Рейз до 2,5 ББ' },
          ],
        },
      ],
    }],
  }
}
