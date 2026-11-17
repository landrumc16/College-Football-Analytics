import { useId, useState } from 'react'
import {
  explainProbability, flipProbabilityInput, flipSpreadInput, headlineProbability,
  moneylineProbability, parseMoneyline, parseProbability, parseSpread, percent, probabilityDifference, signed,
  spreadExample, spreadStory, teamView, toggleSign, type Parsed,
} from './marketCalculator'

export type ModelSource = { kind: 'published' | 'hypothetical'; label: string }
type Props = { home: string; away: string; homeProbability: number; homeMargin: number; source: ModelSource; headingLevel?: 'h2' | 'h3' }

// Entered market numbers live only in this component's state: never in analytics, storage, URLs or requests.
export default function MarketCalculator({ home, away, homeProbability, homeMargin, source, headingLevel = 'h3' }: Props) {
  const id = useId()
  const Heading = headingLevel
  const [team, setTeam] = useState(home)
  const [spread, setSpread] = useState('')
  const [probability, setProbability] = useState('')
  const [moneyline, setMoneyline] = useState('')
  const [moneylineCleared, setMoneylineCleared] = useState(false)
  const selected = team === away ? away : home
  const opponent = selected === home ? away : home
  const model = teamView(home, homeProbability, homeMargin, selected)

  const choose = (next: string) => {
    if (next === selected) return
    setTeam(next)
    setSpread(flipSpreadInput)
    setProbability(flipProbabilityInput)
    setMoneylineCleared(moneyline.trim() !== '')
    setMoneyline('')   // the other side's moneyline cannot be derived: bookmaker margins differ by side
  }

  if (!model) return <section className="market-calculator" aria-labelledby={`${id}-title`}>
    <Heading id={`${id}-title`}>Market Analysis Calculator</Heading>
    <p role="status">Model prediction unavailable for this matchup, so no comparison is shown. The calculator never estimates a missing model value.</p>
  </section>

  const spreadParsed = parseSpread(spread)
  const probabilityParsed = parseProbability(probability)
  const moneylineParsed = parseMoneyline(moneyline)
  const error = (p: Parsed) => !p.ok && 'error' in p ? p.error : null
  const signButton = (label: string, value: string, set: (v: string) => void) =>
    <button type="button" className="market-sign" aria-label={`Switch ${label} sign (plus/minus)`} onClick={() => set(toggleSign(value))}>±</button>

  return <section className="market-calculator" aria-labelledby={`${id}-title`}>
    <Heading id={`${id}-title`}>Market Analysis Calculator</Heading>
    <p className="market-source"><span className={`market-badge ${source.kind}`}>{source.kind === 'published' ? 'Published forecast' : 'Hypothetical matchup'}</span> {source.label}</p>
    <fieldset className="market-team">
      <legend>1. Analyze for</legend>
      {[home, away].map(t => <label key={t} className={selected === t ? 'selected' : undefined}><input type="radio" name={`${id}-team`} value={t} checked={selected === t} onChange={() => choose(t)} />{t}</label>)}
    </fieldset>
    <p className="market-step">2. Type a market number for <strong>{selected}</strong>. Results update as you type. Numbers stay in this browser: nothing is retrieved, verified, saved or sent.</p>
    {moneylineCleared && <p className="market-note" role="status">Moneyline cleared: enter {selected}'s own moneyline. The other side cannot be derived because bookmaker margins differ by side.</p>}
    <div className="market-grid">
      <div className="market-card">
        <label htmlFor={`${id}-spread`}>{selected} point spread</label>
        <div className="market-input-row">
          <input id={`${id}-spread`} inputMode="decimal" autoComplete="off" placeholder="e.g. -7 or +3.5" value={spread}
            onChange={e => setSpread(e.target.value)} aria-describedby={`${id}-spread-help ${id}-spread-out`} aria-invalid={!!error(spreadParsed)} />
          {signButton('spread', spread, setSpread)}
        </div>
        <small id={`${id}-spread-help`}>{spreadExample(selected)}</small>
        <div id={`${id}-spread-out`} aria-live="polite">
          {error(spreadParsed) && <p className="market-error">{error(spreadParsed)}</p>}
          {spreadParsed.ok && (() => {
            const story = spreadStory(selected, opponent, model.margin, spreadParsed.value)
            return <div className="market-result">
              <p className="market-headline"><strong>{story.title}</strong></p>
              <p><strong>Our prediction</strong></p><p>{story.modelText}</p>
              <p><strong>Your entered betting line</strong></p><p>{story.lineText}</p>
              <p><strong>What this means</strong></p><p>{story.meaning}</p>
              <p><strong>Our take</strong></p><p>{story.take}</p>
              <small>Based on our model and the betting line you entered, not a verified live market line. Educational comparison only.</small>
            </div>
          })()}
        </div>
      </div>
      <div className="market-card">
        <label htmlFor={`${id}-probability`}>{selected} prediction-market win probability (%)</label>
        <input id={`${id}-probability`} inputMode="decimal" autoComplete="off" placeholder="0 to 100, e.g. 62" value={probability}
          onChange={e => setProbability(e.target.value)} aria-describedby={`${id}-probability-help ${id}-probability-out`} aria-invalid={!!error(probabilityParsed)} />
        <small id={`${id}-probability-help`}>The chance the market gives {selected} to win, as you read it.</small>
        <div id={`${id}-probability-out`} aria-live="polite">
          {error(probabilityParsed) && <p className="market-error">{error(probabilityParsed)}</p>}
          {probabilityParsed.ok && <Result headline={headlineProbability(selected, model.probability, probabilityParsed.value)} rows={[
            ['Our model', `${percent(model.probability)} ${selected} win probability`],
            ['You entered', percent(probabilityParsed.value)],
            ['Difference', `${signed(probabilityDifference(model.probability, probabilityParsed.value))} percentage points`],
          ]} text={explainProbability(selected, model.probability, probabilityParsed.value, 'prediction market')} />}
        </div>
      </div>
      <div className="market-card">
        <label htmlFor={`${id}-moneyline`}>{selected} American moneyline</label>
        <div className="market-input-row">
          <input id={`${id}-moneyline`} inputMode="decimal" autoComplete="off" placeholder="e.g. -150 or +130" value={moneyline}
            onChange={e => { setMoneyline(e.target.value); setMoneylineCleared(false) }} aria-describedby={`${id}-moneyline-help ${id}-moneyline-out`} aria-invalid={!!error(moneylineParsed)} />
          {signButton('moneyline', moneyline, v => { setMoneyline(v); setMoneylineCleared(false) })}
        </div>
        <small id={`${id}-moneyline-help`}>Raw implied probability. The bookmaker's margin (vig) is <strong>not removed</strong>, so it usually overstates each side's chance.</small>
        <div id={`${id}-moneyline-out`} aria-live="polite">
          {error(moneylineParsed) && <p className="market-error">{error(moneylineParsed)}</p>}
          {moneylineParsed.ok && (() => { const raw = moneylineProbability(moneylineParsed.value); return <Result headline={headlineProbability(selected, model.probability, raw)} rows={[
            ['Our model', `${percent(model.probability)} ${selected} win probability`],
            ['You entered', `${signed(moneylineParsed.value, 0)} → ${percent(raw)} raw implied`],
            ['Difference', `${signed(probabilityDifference(model.probability, raw))} percentage points`],
          ]} text={explainProbability(selected, model.probability, raw, 'moneyline')} /> })()}
        </div>
      </div>
    </div>
    <p className="market-disclaimer">Opponent: {opponent}. A difference is not a forecast of profit or a recommendation to wager. Markets can reflect information the model lacks, and bookmaker margins mean a difference can still lose money. Educational comparison only.</p>
  </section>
}

function Result({ headline, rows, text }: { headline: string; rows: [string, string][]; text: string }) {
  return <div className="market-result">
    <p className="market-headline"><strong>{headline}</strong></p>
    <dl>{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
    <p>{text}</p>
    <small>Market number entered by you; not retrieved or verified by this app.</small>
  </div>
}
