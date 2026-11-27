export type Favorites = (string | null)[];
export const FAVORITES_KEY = 'cfba-favorites-v1';
export function primaryFavorite(favorites: Favorites): string | null {
    return favorites.find((team): team is string => typeof team === 'string' && team.trim().length > 0) ?? null;
}
// Verified display-name pairs already used by cfp_publish.py/pipeline.py; never use fuzzy matches.
export const SCHOOL_DISPLAY_NAMES: Record<string,string> = {
  'Miami (FL)':'Miami', 'Appalachian State':'App State', 'Sam Houston State':'Sam Houston', 'ULM':'UL Monroe',
}
export function eligibleSchool(team:string|null, eligible:readonly string[]):string|null {
  if (!team) return null
  if (eligible.includes(team)) return team
  for (const [canonical,display] of Object.entries(SCHOOL_DISPLAY_NAMES)) {
    const other=team===canonical?display:team===display?canonical:null
    if(other && eligible.includes(other)) return other
  }
  return null
}
export const withSchoolAliases=(schools:readonly string[])=>schools.flatMap(team=>[team,...(SCHOOL_DISPLAY_NAMES[team]?[SCHOOL_DISPLAY_NAMES[team]]:[])])
export function defaultSchool(primary: string | null, eligible: readonly string[], fallback = ''): string {
    return eligibleSchool(primary,eligible) ?? fallback;
}
export function favoriteGame(primary: string | null, games: readonly {
    game_id: number;
    home: string;
    away: string;
    week?: number;
    start_date?: string | null;
}[]): string {
    const matches = games.filter(g => eligibleSchool(primary,[g.home,g.away]) !== null);
    matches.sort((a, b) => (a.week ?? 0) - (b.week ?? 0) || (a.start_date ?? '').localeCompare(b.start_date ?? '') || a.game_id - b.game_id);
    return matches.length ? String(matches[0].game_id) : '';
}
export type DefaultSelection = {
    value: string | null;
    primary: string | null;
};
export function resolveFavoriteSelection(selection: DefaultSelection, primary: string | null, navigation: number, changedAt: number, eligible: readonly string[], fallback: string, preferred: string | undefined = undefined, allowQuery = false): string {
    const rebase = selection.primary !== primary && navigation > changedAt;
    const value = rebase ? null : selection.value;
    if (value !== null) {
        if (allowQuery || value === '' || !eligible.length) return value;
        const option=eligibleSchool(value,eligible);
        if (option) return option;
    }
    // Keep the active view's old default until the next navigation after a favorite change.
    const seed = rebase ? primary : selection.primary;
    return defaultSchool(preferred === undefined ? seed : preferred, eligible, fallback);
}
