# Secondary navigation refinement

`SectionTabs` now supplies a native labelled select below 768px. At larger sizes
it retains the existing horizontal keyboard-operable tabs if the entire row fits;
otherwise it supplies the same select. A ResizeObserver measures the actual tab
row and its container, so nested Profile navigation, browser zoom, font changes
and viewport resizing do not require horizontal discovery. The inactive row is
hidden from assistive technology and the keyboard while remaining measurable.
Panels use the current selection as their accessible name in dropdown mode.

All destinations and all four Profile sections share this component. Selection
uses the original callbacks and state: favorites, comparisons, prediction links
and the homepage historical spotlight still choose the same school and section.
The five-destination bottom bar, pages, data, engine and PWA are unchanged.

The V5 acceptance workflow builds the real app and runs the full regression and
browser journeys at 375/390/430/768/1536px. The shared browser helper exercises the
visible select or tabs, including native keyboard behavior, desktop arrow/Home/End,
all destinations, four Profile sections and phone/desktop resize without losing
selection. Actual secondary and Profile screenshots are retained with the tested
SHA in the acceptance artifact. Android Chrome emulation checks installability,
updates, offline fallback and recovery. Merge requires explicit owner approval.
