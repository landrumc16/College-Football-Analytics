export type Favorites = (string | null)[];
export const FAVORITES_KEY = 'cfba-favorites-v1';
export function primaryFavorite(favorites: Favorites): string | null {
    return favorites.find((team): team is string => typeof team === 'string' && team.trim().length > 0) ?? null;
}
export function defaultSchool(primary: string | null, eligible: readonly string[], fallback = ''): string {
    return primary && eligible.includes(primary) ? primary : fallback;
}
export function favoriteGame(primary: string | null, games: readonly {
    game_id: number;
    home: string;
    away: string;
    week?: number;
    start_date?: string | null;
}[]): string {
    const matches = games.filter(g => primary && (g.home === primary || g.away === primary));
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
    if (value !== null && (allowQuery || value === '' || !eligible.length || eligible.includes(value)))
        return value;
    // Keep the active view's old default until the next navigation after a favorite change.
    const seed = rebase ? primary : selection.primary;
    return defaultSchool(preferred === undefined ? seed : preferred, eligible, fallback);
}
