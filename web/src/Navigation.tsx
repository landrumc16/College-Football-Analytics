export const destinations = [
  { id: 'home', label: 'Home', views: [{ id: 'home', label: 'This Week' }, { id: 'predictions', label: 'Game Predictions' }] },
  { id: 'rankings', label: 'Rankings', views: [{ id: 'rankings', label: 'Model Rankings' }, { id: 'ap', label: 'AP Poll' }, { id: 'coaches', label: 'Coaches Poll' }, { id: 'stock', label: 'Team Stock Watch' }] },
  { id: 'teams', label: 'Teams', views: [{ id: 'profile', label: 'Team Profiles' }, { id: 'compare', label: 'Compare & What If' }, { id: 'programs', label: 'Program Directory' }, { id: 'hype', label: 'Hype Index' }, { id: 'trajectory', label: 'Program Trajectory' }] },
  { id: 'playoffs', label: 'Playoffs', views: [{ id: 'cfp', label: 'CFP Projections' }, { id: 'conferences', label: 'Conference Races' }, { id: 'contenders', label: 'Contenders & Pretenders' }] },
  { id: 'research', label: 'Research', views: [{ id: 'research', label: 'Prediction Accuracy' }, { id: 'history', label: 'Historical Research' }, { id: 'methods', label: 'Methodology' }, { id: 'sources', label: 'Data Sources' }, { id: 'validation', label: 'Model Validation' }] },
] as const

export type View = typeof destinations[number]['views'][number]['id']
export type Destination = typeof destinations[number]['id']

export function PrimaryNavigation({ value, onChange }: { value: Destination; onChange: (destination: Destination) => void }) {
  return <nav className="primary-navigation" aria-label="Main navigation">
    <label className="mobile-primary-navigation"><span>Destination</span>
      <select aria-label="Choose main destination" value={value} onChange={event => onChange(event.target.value as Destination)}>
        {destinations.map(destination => <option key={destination.id} value={destination.id}>{destination.label}</option>)}
      </select>
    </label>
    <div className="primary-destinations">
      {destinations.map(destination => <button type="button" key={destination.id}
        aria-current={value === destination.id ? 'page' : undefined}
        onClick={() => onChange(destination.id)}>{destination.label}</button>)}
    </div>
  </nav>
}

/** Native buttons plus the standard arrow/Home/End tab keyboard interaction. */
export function SectionTabs({ label, items, value, onChange, panelId }: {
  label: string; items: readonly { id: string; label: string }[]; value: string;
  onChange: (value: string) => void; panelId: string;
}) {
  return <div className="section-tabs" role="tablist" aria-label={label}>
    {items.map((item, index) => <button type="button" role="tab" key={item.id}
      id={`${panelId}-${item.id}`} aria-controls={panelId} aria-selected={value === item.id}
      tabIndex={value === item.id ? 0 : -1} onClick={() => onChange(item.id)}
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
}
