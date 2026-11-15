// First-visit analytics consent helpers for browser tests.
export const CHOICE_KEY = 'cfba-analytics-choice-v1';
const seedDeclined = key => { try { if (localStorage.getItem(key) === null) localStorage.setItem(key, '"off"'); } catch { /* blocked storage */ } };

// Tests unrelated to analytics start as a visitor who already chose "No thanks"
// (the same stored state the prompt writes), so the modal cannot cover their journeys.
export function startAsDeclinedVisitor(browser) {
  const newContext = browser.newContext.bind(browser);
  browser.newContext = async (options) => { const context = await newContext(options); await context.addInitScript(seedDeclined, CHOICE_KEY); return context; };
  browser.newPage = async (options) => { const context = await browser.newContext(options); const page = await context.newPage(); page.on('close', () => context.close().catch(() => {})); return page; };
  return browser;
}

export const consentDialog = page => page.getByRole('dialog', { name: 'Help improve College Football Analytics', exact: true });
export async function answerConsentPrompt(page, allow) {
  const dialog = consentDialog(page);
  await dialog.waitFor();
  await dialog.getByRole('button', { name: allow ? 'Allow analytics for this visit' : 'No thanks', exact: true }).click();
  await dialog.waitFor({ state: 'detached' });
}
