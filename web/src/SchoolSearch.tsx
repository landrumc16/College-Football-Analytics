import { useId, useLayoutEffect, useRef, useState } from 'react'
import { exactSchool, rankSchools } from './schoolSearch'
import './school-search.css'

type Props = {
  label: string                       // visible label; also the accessible name tests and screen readers use
  schools: string[]
  value: string                       // the selected school ('' = none)
  onChange: (school: string) => void
  placeholder?: string
  commitOnExactMatch?: boolean        // pickers that confirm with a separate button (Favorites) select on an exact typed name
  className?: string
}

/** Accessible combobox for choosing one school: type, see ranked suggestions, pick by touch, Enter or arrows. */
export default function SchoolSearch({ label, schools, value, onChange, placeholder = 'Search for a school...', commitOnExactMatch = false, className }: Props) {
  const id = useId()
  const input = useRef<HTMLInputElement>(null)
  const [editing, setEditing] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const matches = editing ? rankSchools(query, schools) : []
  const listId = `${id}-list`
  // Confirm-later pickers (Favorites): an exact typed name is the selection, so close the list and uncover the confirm button.
  const exactHit = commitOnExactMatch && editing ? exactSchool(query, schools) : null
  const open = editing && query.trim() !== '' && !exactHit
  // After a choice focus stays in the field with the name selected, so typing again starts a new search.
  const choose = (school: string) => { onChange(school); setEditing(false); setQuery(''); setActive(0); reselect.current = true }
  const list = useRef<HTMLUListElement>(null)
  const reselect = useRef(false)
  useLayoutEffect(() => {
    if (reselect.current && document.activeElement === input.current) input.current?.select()
    reselect.current = false
  })
  // Keep the open list fully on screen: scroll just enough that it clears the fixed bottom navigation on phones.
  useLayoutEffect(() => {
    const el = list.current
    if (!el) return
    const nav = document.querySelector('.editorial-navigation')
    const navTop = nav && getComputedStyle(nav).position === 'fixed' ? nav.getBoundingClientRect().top : window.innerHeight
    const overlap = el.getBoundingClientRect().bottom + 8 - navTop
    const room = (input.current?.getBoundingClientRect().top ?? 0) - 8
    if (overlap > 0) window.scrollBy(0, Math.min(overlap, Math.max(room, 0)))
  }, [open, matches.length])
  const stop = () => { setEditing(false); setQuery(''); setActive(0) }
  return <div className={`school-search${className ? ' ' + className : ''}`}>
    <label htmlFor={`${id}-input`}>{label}</label>
    <div className="school-search-field">
      <input ref={input} id={`${id}-input`} type="text" role="combobox" autoComplete="off" spellCheck={false}
        aria-autocomplete="list" aria-expanded={open && matches.length > 0} aria-controls={listId}
        aria-activedescendant={open && matches.length ? `${id}-opt-${active}` : undefined}
        aria-describedby={`${id}-status`} placeholder={value && !editing ? undefined : placeholder}
        value={editing ? query : value}
        onFocus={() => { setEditing(true); setQuery('') }}
        onClick={() => { if (!editing) { setEditing(true); setQuery('') } }}
        onBlur={stop}
        onChange={e => {
          setEditing(true); setQuery(e.target.value); setActive(0)
          if (commitOnExactMatch) onChange(exactSchool(e.target.value, schools) ?? '')
        }}
        onKeyDown={e => {
          if (e.key === 'ArrowDown' && matches.length) { e.preventDefault(); setActive(i => (i + 1) % matches.length) }
          else if (e.key === 'ArrowUp' && matches.length) { e.preventDefault(); setActive(i => (i - 1 + matches.length) % matches.length) }
          else if (e.key === 'Enter' && open && matches.length) { e.preventDefault(); choose(matches[Math.min(active, matches.length - 1)]) }
          else if (e.key === 'Escape') { e.preventDefault(); stop(); input.current?.blur() }
        }} />
      {open && matches.length > 0 && <ul ref={list} id={listId} role="listbox" aria-label="Suggested schools" className="school-search-list">
        {matches.map((school, i) => <li key={school} id={`${id}-opt-${i}`} role="option" aria-selected={i === active}
          className={i === active ? 'active' : undefined} onMouseDown={e => e.preventDefault()} onClick={() => choose(school)}>{school}</li>)}
      </ul>}
    </div>
    {/* One line at a constant height: a status that grows or shrinks on blur would move the buttons below it mid-click. */}
    <p id={`${id}-status`} className="school-search-status" role="status">
      {exactHit ? <>Selected: <strong>{exactHit}</strong></> : editing ? ((value ? `Current: ${value} · ` : '') + (!query.trim() ? 'type a school name or abbreviation, like TTU' :
        matches.length ? `${matches.length} found` : `no match for “${query.trim()}”`)).replace(/^./, c => c.toUpperCase())
        : value ? <>Selected: <strong>{value}</strong></> : ''}
    </p>
  </div>
}
