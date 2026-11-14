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
    const layout = await tabs.evaluate(row => ({ width: row.scrollWidth, available: row.parentElement.clientWidth - 6,
      top: [...row.children].map(tab => tab.getBoundingClientRect().top) }));
    assert.ok(layout.width <= layout.available && layout.top.every(y => Math.abs(y-layout.top[0]) < 1), JSON.stringify(layout));
  }
  return dropdown;
}
