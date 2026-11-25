import { titleCase } from './titleCase'
import type { ReactNode } from 'react'
import './stat-explain.css'

/** One-sentence plain-English takeaway shown above a group of visible statistics. */
export function Takeaway({ children }: { children: ReactNode }) {
  return <p className="stat-takeaway">{children}</p>
}

/** The standard collapsed explanation shown below a group of statistics. */
export function StatExplain({ children, label = 'What Do These Numbers Mean?' }: { children: ReactNode; label?: string }) {
  return <details className="stat-explain"><summary>{titleCase(label)}</summary><div className="stat-explain-body">{children}</div></details>
}
