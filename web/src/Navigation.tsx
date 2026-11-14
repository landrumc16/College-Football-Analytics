import { useLayoutEffect, useRef, useState } from 'react'
import './secondary-navigation.css'

export const destinations = [
  { id: 'home', label: 'Home', views: [{ id: 'home', label: 'This Week' }, { id: 'predictions', label: 'Game Predictions' }] },
  { id: 'rankings', label: 'Rankings', views: [{ id: 'rankings', label: 'Model Rankings' }, { id: 'ap', label: 'AP Poll' }, { id: 'coaches', label: 'Coaches Poll' }, { id: 'stock', label: 'Team Stock Watch' }] },
  { id: 'teams', label: 'Teams', views: [{ id: 'profile', label: 'Team Profiles' }, { id: 'compare', label: 'Compare & What If' }, { id: 'programs', label: 'Program Directory' }, { id: 'hype', label: 'Hype Index' }, { id: 'trajectory', label: 'Program Trajectory' }] },
  { id: 'playoffs', label: 'Playoffs', views: [{ id: 'cfp', label: 'CFP Projections' }, { id: 'conferences', label: 'Conference Races' }, { id: 'contenders', label: 'Contenders & Pretenders' }] },
  { id: 'research', label: 'Research', views: [{ id: 'research', label: 'Prediction Accuracy' }, { id: 'history', label: 'Historical Research' }, { id: 'methods', label: 'Methodology' }, { id: 'sources', label: 'Data Sources' }, { id: 'validation', label: 'Model Validation' }] },
] as const

export type View = typeof destinations[number]['views'][number]['id']

/** Native buttons plus the standard arrow/Home/End tab keyboard interaction. */
export function SectionTabs({ label, items, value, onChange, panelId, onDropdownChange }: {
  label: string; items: readonly { id: string; label: string }[]; value: string;
  onChange: (value: string) => void; panelId: string; onDropdownChange: (dropdown: boolean) => void;
}) {
  const container = useRef<HTMLDivElement>(null)
  const tabs = useRef<HTMLDivElement>(null)
  const [dropdown, setDropdown] = useState(() => window.matchMedia('(max-width: 767px)').matches)
  useLayoutEffect(() => {
    const phone = window.matchMedia('(max-width: 767px)')
    const measure = () => {
      if (!container.current || !tabs.current) return
      const style = getComputedStyle(container.current)
      const available = container.current.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)
      const next = phone.matches || tabs.current.scrollWidth > available
      setDropdown(next)
      onDropdownChange(next)
    }
    const observer = new ResizeObserver(measure)
    observer.observe(container.current!)
    observer.observe(tabs.current!)
    phone.addEventListener('change', measure)
    measure()
    return () => { observer.disconnect(); phone.removeEventListener('change', measure) }
  }, [items, onDropdownChange])
  return <div className="secondary-navigation" ref={container}>
    <span className="secondary-selection" id={`${panelId}-selection`}>{items.find(item => item.id === value)?.label}</span>
    <label className="secondary-picker" hidden={!dropdown}>
      <span className="secondary-selection">{label}</span>
      <select aria-label={label} aria-controls={panelId} value={value} onChange={event => onChange(event.target.value)}>
        {items.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}
      </select>
    </label>
    <div className="section-tabs" ref={tabs} role="tablist" aria-label={label} aria-hidden={dropdown || undefined} data-measuring={dropdown || undefined}>
    {items.map((item, index) => <button type="button" role="tab" key={item.id}
      id={`${panelId}-${item.id}`} aria-controls={panelId} aria-selected={value === item.id}
      tabIndex={!dropdown && value === item.id ? 0 : -1} onClick={() => onChange(item.id)}
      onKeyDown={event => {
        const next = event.key === 'ArrowRight' ? (index + 1) % items.length
          : event.key === 'ArrowLeft' ? (index + items.length - 1) % items.length
          : event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : null
        if (next == null) return
        event.preventDefault()
        const buttons = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
        buttons?.[next].focus()
        onChange(items[next].id)
      }}>{item.label}</button>)}
    </div>
  </div>
}
