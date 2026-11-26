import { Component, type ReactNode } from 'react'

/** Keep a malformed optional publication from taking down the rest of the app. */
export default class DataBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    if (this.state.failed) return <section className="notice" role="alert">
      <strong>This Section Is Unavailable</strong>
      <p>Its published data could not be displayed. The rest of the app remains available.</p>
      <button type="button" onClick={() => this.setState({ failed: false })}>Retry Loading Data</button>
    </section>
    return this.props.children
  }
}
