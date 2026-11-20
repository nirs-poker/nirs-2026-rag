import type { Ref } from 'react'
import { formatBB, type Hand } from '../modules/chatTypes'
import { PlayingCard, PokerTable } from './PokerTable'

interface Props {
  hand: Hand
  sectionRef: Ref<HTMLElement>
  onStep: (step: number) => void
  onGoToHand: () => void
}

export function HandTable({ hand, sectionRef, onStep, onGoToHand }: Props) {
  const { stepIndex, steps } = hand
  const step = steps[stepIndex]
  const playerSteps = steps
    .map((step, index) => ({ ...step, index }))
    .filter(({ quality, index }) => quality !== 'opponent' && !(hand.setup && index === 0))
  if (!step) return null
  return (
    <section className="hand-view" id="review-table" ref={sectionRef} tabIndex={-1} aria-label="Стол">
      <div className={`step-state${playerSteps.length ? '' : ' empty-steps'}`}>
        <div className="step-dots" role="group" aria-label="Действия игрока">
          {playerSteps.map(({ label, quality, index }) => (
            <button
              key={index}
              type="button"
              className={`step-dot ${quality ?? ''}${index === stepIndex ? ' current' : ''}`}
              title={label}
              aria-label={`Ход ${index + 1}. ${label}`}
              aria-pressed={index === stepIndex}
              onClick={() => onStep(index)}
            />
          ))}
        </div>
      </div>
      <PokerTable
        board={step.board}
        pot={<div className="pot">{step.pot === null ? 'Банк не указан' : `Банк ${formatBB(step.pot)}`}</div>}
        cards={hand.cards.map(card => <PlayingCard key={card} card={card} />)}
        hero={<div><b>Вы · {hand.heroPosition}</b><span>{step.hero}</span></div>}
        opponent={<div><b>Соперник · {hand.opponentPosition}</b><span>{step.opponent}</span></div>}
        dealerPosition={hand.heroPosition === 'BTN' ? 'hero' : hand.opponentPosition === 'BTN' ? 'opponent' : undefined}
      />
      <div className="hand-controls">
        <div className="step-nav">
          <button className="control" type="button" disabled={stepIndex === 0} onClick={() => onStep(stepIndex - 1)}>← Назад</button>
          <button className="control" type="button" disabled={stepIndex === steps.length - 1} onClick={() => onStep(stepIndex + 1)}>Вперёд →</button>
        </div>
        <button className="control message-link" type="button" onClick={onGoToHand}>К раздаче {Boolean(hand.unread) && <span className="unread">{hand.unread}</span>}</button>
      </div>
    </section>
  )
}
