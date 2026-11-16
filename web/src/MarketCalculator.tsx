import { useId, useState } from 'react'
import {
  explainProbability, explainSpread, flipProbabilityInput, flipSpreadInput, moneylineProbability, parseMoneyline,
  parseProbability, parseSpread, percent, probabilityDifference, signed, spreadDifference, teamView, type Parsed,
} from './marketCalculator'

export type ModelSource = { kind: 'published' | 'hypothetical'; label: string }
type Props = { home: string; away: string; homeProbability: number; homeMargin: number; source: ModelSource }

// Entered market numbers live only in this component's state: never in analytics, storage, URLs or requests.
export default function MarketCalculator({ home, away, homeProbability, homeMargin, source }: Props) {
  const id = useId()
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
    <h3 id={`${id}-title`}>Market Analysis Calculator</h3>
    <p role="status">Model prediction unavailable for this matchup, so no comparison is shown. The calculator never estimates a missing model value.</p>
  </section>

  const spreadParsed = parseSpread(spread)
  const probabilityParsed = parseProbability(probability)
  const moneylineParsed = parseMoneyline(moneyline)
  const error = (p: Parsed) => !p.ok && 'error' in p ? p.error : null

  return <section className="market-calculator" aria-labelledby={`${id}-title`}>
    <h3 id={`${id}-title`}>Market Analysis Calculator</h3>
    <p>Enter a market number you have seen to compare it with our model. <strong>Numbers you enter stay in this browser:</strong> the app does not retrieve, verify, save or send them.</p>
    <p className="market-source"><span className={`market-badge ${source.kind}`}>{source.kind === 'published' ? 'Published forecast' : 'Hypothetical matchup'}</span> {source.label}</p>
    <fieldset className="market-team">
      <legend>Compare from the perspective of</legend>
      {[home, away].map(t => <label key={t}><input type="radio" name={`${id}-team`} value={t} checked={selected === t} onChange={() => choose(t)} />{t}</label>)}
    </fieldset>
    {moneylineCleared && <p className="market-note" role="status">Moneyline cleared: enter {selected}'s own moneyline. The other side cannot be derived because bookmaker margins differ by side.</p>}
    <div className="market-grid">
      <div className="market-card">
        <label htmlFor={`${id}-spread`}>{selected} point spread</label>
        <input id={`${id}-spread`} inputMode="decimal" autoComplete="off" placeholder="e.g. -7 or +3.5" value={spread}
          onChange={e => setSpread(e.target.value)} aria-describedby={`${id}-spread-help ${id}-spread-out`} aria-invalid={!!error(spreadParsed)} />
        <small id={`${id}-spread-help`}>Negative means {selected} is favoured; positive means {selected} is the underdog.</small>
        <div id={`${id}-spread-out`} aria-live="polite">
          {error(spreadParsed) && <p className="market-error">{error(spreadParsed)}</p>}
          {spreadParsed.ok && <Result rows={[
            ['Our model', `${selected} ${signed(model.margin)} projected margin`],
            ['You entered', `${selected} ${spreadParsed.value === 0 ? 'PK (0)' : signed(spreadParsed.value)}`],
            ['Difference', `${signed(spreadDifference(model.margin, spreadParsed.value))} points`],
          ]} text={explainSpread(selected, model.margin, spreadParsed.value)} />}
        </div>
      </div>
      <div className="market-card">
        <label htmlFor={`${id}-probability`}>{selected} prediction-market win probability (%)</label>
        <input id={`${id}-probability`} inputMode="decimal" autoComplete="off" placeholder="0 to 100, e.g. 62" value={probability}
          onChange={e => setProbability(e.target.value)} aria-describedby={`${id}-probability-help ${id}-probability-out`} aria-invalid={!!error(probabilityParsed)} />
        <small id={`${id}-probability-help`}>The chance the market gives {selected} to win, as you read it.</small>
        <div id={`${id}-probability-out`} aria-live="polite">
          {error(probabilityParsed) && <p className="market-error">{error(probabilityParsed)}</p>}
          {probabilityParsed.ok && <Result rows={[
            ['Our model', `${percent(model.probability)} ${selected} win probability`],
            ['You entered', percent(probabilityParsed.value)],
            ['Difference', `${signed(probabilityDifference(model.probability, probabilityParsed.value))} percentage points`],
          ]} text={explainProbability(selected, model.probability, probabilityParsed.value, 'prediction market')} />}
        </div>
      </div>
      <div className="market-card">
        <label htmlFor={`${id}-moneyline`}>{selected} American moneyline</label>
        <input id={`${id}-moneyline`} inputMode="decimal" autoComplete="off" placeholder="e.g. -150 or +130" value={moneyline}
          onChange={e => { setMoneyline(e.target.value); setMoneylineCleared(false) }} aria-describedby={`${id}-moneyline-help ${id}-moneyline-out`} aria-invalid={!!error(moneylineParsed)} />
        <small id={`${id}-moneyline-help`}>Raw implied probability. The bookmaker's margin (vig) is <strong>not removed</strong>, so it usually overstates each side's chance.</small>
        <div id={`${id}-moneyline-out`} aria-live="polite">
          {error(moneylineParsed) && <p className="market-error">{error(moneylineParsed)}</p>}
          {moneylineParsed.ok && (() => { const raw = moneylineProbability(moneylineParsed.value); return <Result rows={[
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

function Result({ rows, text }: { rows: [string, string][]; text: string }) {
  return <div className="market-result">
    <dl>{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
    <p>{text}</p>
    <small>Market number entered by you; not retrieved or verified by this app.</small>
  </div>
}
