import type { ReactNode } from 'react'
import dealer from '../../img/dealer.png'
import opponentImage from '../../img/opponent.png'
import { suits, type Card, type Suit } from '../modules/chatTypes'

export function PlayingCard({ card }: { card: Card }) {
  const suit = card[1] as Suit
  return <span className={`pcard${suit === 'h' || suit === 'd' ? ' r' : ''}`}>{card[0]}<small>{suits[suit]}</small></span>
}

interface Props {
  board?: Card[]
  renderBoardSlot?: (index: number) => ReactNode
  pot: ReactNode
  cards: ReactNode
  hero: ReactNode
  opponent: ReactNode
  dealerPosition?: string
  setup?: boolean
}

export function PokerTable({ board = [], renderBoardSlot, pot, cards, hero, opponent, dealerPosition, setup = false }: Props) {
  const streets = [
    { name: 'Флоп', from: 0, count: 3 },
    { name: 'Тёрн', from: 3, count: 1 },
    { name: 'Ривер', from: 4, count: 1 },
  ]
  return (
    <div className={setup ? 'scene empty-table' : 'scene'} role="group" aria-label="Покерный стол">
      <div className="poker-table">
        <div className="felt">
          <div className="bet-line" />
          {pot}
          <div className="board">
            {streets.map(({ name, from, count }) => (
              <div className="street" key={name}>
                <div className="street-slots">
                  {Array.from({ length: count }, (_, index) => {
                    if (renderBoardSlot) return renderBoardSlot(from + index)
                    const card = board[from + index]
                    return card ? <PlayingCard key={index} card={card} /> : <span key={index} className="slot" aria-hidden="true" />
                  })}
                </div>
                <div className="street-name">{name}</div>
              </div>
            ))}
          </div>
          {setup && <div className="dealer-btn setup-dealer-hero" title="Баттон у вас">D</div>}
          {setup && <div className="dealer-btn setup-dealer-opp" title="Баттон у соперника">D</div>}
          {!setup && dealerPosition && <div className={`dealer-btn ${dealerPosition === 'hero' ? 'dealer-hero' : ''}`} title="Баттон">D</div>}
          <div className="opp-cards" aria-label="Карты соперника закрыты" role="img"><span className="back" /><span className="back" /></div>
          <div className="hero-box" role="group" aria-label="Ваши карты">{cards}</div>
        </div>
        <div className="seat s-dealer"><img className="figure" src={dealer} alt="" /><div><b>Дилер</b></div></div>
        <div className="seat s-hero hero"><span className="ava ava-me" aria-hidden="true">С</span>{hero}</div>
        <div className="seat s-opp"><img className="figure" src={opponentImage} alt="" />{opponent}</div>
      </div>
    </div>
  )
}
