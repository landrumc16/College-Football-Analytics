import { defineConfig, loadEnv } from 'vite'
export default defineConfig(({ mode }) => {
  const env = { ...loadEnv(mode, process.cwd(), 'VITE_'), ...process.env }
  const key = env.VITE_POSTHOG_PUBLIC_KEY || '', host = env.VITE_POSTHOG_HOST || ''
  // Fail before bundling; a runtime guard alone would still expose an invalid secret in JS.
  if (key && !/^phc_[a-zA-Z0-9]{10,}$/.test(key)) throw Error('Analytics requires a public project token; refusing to bundle another key type.')
  if ((key || host) && (!key || !['https://us.i.posthog.com', 'https://eu.i.posthog.com'].includes(host))) throw Error('Analytics public token and regional ingestion host must both be configured.')
  return { base: './' }
})
