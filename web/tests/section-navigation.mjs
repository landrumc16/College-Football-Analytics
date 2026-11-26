import assert from 'node:assert/strict';

export async function chooseSection(page, group, label) {
  const picker = page.getByRole('combobox', { name: group, exact: true });
  if (await picker.isVisible()) await picker.selectOption({ label });
  else await page.getByRole('tablist', { name: group, exact: true }).getByRole('tab', { name: label, exact: true }).click();
  await assertSection(page, group, label);
}

export async function assertSection(page, group, label) {
  const picker = page.getByRole('combobox', { name: group, exact: true });
  if (await picker.isVisible()) assert.equal(await picker.locator('option:checked').textContent(), label);
  else await page.getByRole('tablist', { name: group, exact: true }).getByRole('tab', { name: label, exact: true, selected: true }).waitFor();
}

export async function assertNavigationFits(page, group, width) {
  const picker = page.getByRole('combobox', { name: group, exact: true });
  const dropdown = await picker.isVisible();
  if (width < 768) assert.ok(dropdown, `${group} must be a phone dropdown`);
  if (dropdown) {
    const box = await picker.boundingBox();
    assert.ok(box && box.x >= 0 && box.x + box.width <= width + 1 && box.height >= 44, JSON.stringify(box));
    assert.equal(await page.getByRole('tablist', { name: group, exact: true }).count(), 0);
  } else {
    const tabs = page.getByRole('tablist', { name: group, exact: true });
    const layout = await tabs.evaluate(row => {
      const container = row.parentElement, style = getComputedStyle(container);
      return { width: row.scrollWidth, available: container.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
        top: [...row.children].map(tab => tab.getBoundingClientRect().top) };
    });
    assert.ok(layout.width <= layout.available && layout.top.every(y => Math.abs(y-layout.top[0]) < 1), JSON.stringify(layout));
  }
  return dropdown;
}

// Bottom navigation (V9) is Home | Rankings | Teams | Playoffs | Research. Market Intelligence is a Research section,
// so 'Market' opens Research and selects it. 'Research & Data' also remains in the top menu.
export const PRIMARY = ['Home', 'Rankings', 'Teams', 'Playoffs', 'Research'];
export async function openDestination(page, name) {
  const nav = page.getByRole('navigation', { name: 'Main navigation', exact: true });
  if (name === 'Market') {
    await nav.getByRole('button', { name: 'Research', exact: true }).click();
    await chooseSection(page, 'Research sections', 'Market Intelligence');
    return;
  }
  await nav.getByRole('button', { name, exact: true }).click();
}

// Choose a school in either the released <select> or the shared SchoolSearch combobox (type, then pick the suggestion).
export async function chooseSchool(page, label, team) {
  const field = page.getByLabel(label).locator('visible=true').first();
  if (await field.evaluate(e => e.tagName) === 'SELECT') return field.selectOption(team);
  if (!team) { await field.focus(); await field.press('Escape'); return; }   // comboboxes keep their selection
  await field.fill(team);
  const list = page.locator(`#${await field.getAttribute('aria-controls')}`.replace(/:/g, '\\:'));
  await list.getByRole('option', { name: team, exact: true }).click();
}
