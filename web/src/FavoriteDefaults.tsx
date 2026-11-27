import { createContext, useCallback, useContext, useEffect, useReducer, useState, type ReactNode, type SetStateAction } from 'react';
import { FAVORITES_KEY, primaryFavorite, resolveFavoriteSelection, type Favorites, type DefaultSelection } from './favoriteDefaults';
type State = {
    favorites: Favorites;
    navigation: number;
    changedAt: number;
    selections: Record<string, DefaultSelection>;
};
type Action = {
    type: 'navigate';
} | {
    type: 'favorites';
    update: SetStateAction<Favorites>;
} | {
    type: 'selection';
    scope: string;
    selection: DefaultSelection;
};
function readFavorites(): State {
    let favorites: Favorites = [null, null, null];
    try {
        const saved = JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]');
        if (Array.isArray(saved))
            favorites = Array.from({ length: 3 }, (_, i) => typeof saved[i] === 'string' ? saved[i] : null);
    }
    catch { /* Preserve the existing empty fallback when storage is blocked or malformed. */ }
    return { favorites, navigation: 0, changedAt: 0, selections: {} };
}
function reduce(state: State, action: Action): State {
    if (action.type === 'selection')
        return { ...state, selections: { ...state.selections, [action.scope]: action.selection } };
    if (action.type === 'navigate')
        return { ...state, navigation: state.navigation + 1 };
    const favorites = typeof action.update === 'function' ? action.update(state.favorites) : action.update;
    return { ...state, favorites, changedAt: primaryFavorite(favorites) === primaryFavorite(state.favorites) ? state.changedAt : state.navigation };
}
const Context = createContext({ favorites: [] as Favorites, primary: null as string | null, navigation: 0, changedAt: 0,
    selections: {} as Record<string, DefaultSelection>, remember: (_scope: string, _selection: DefaultSelection) => { },
    setFavorites: (_update: SetStateAction<Favorites>) => { }, beginNavigation: () => { } });
export function FavoriteDefaultsProvider({ children }: {
    children: ReactNode;
}) {
    const [state, dispatch] = useReducer(reduce, undefined, readFavorites);
    const setFavorites = useCallback((update: SetStateAction<Favorites>) => dispatch({ type: 'favorites', update }), []);
    const remember = useCallback((scope: string, selection: DefaultSelection) => dispatch({ type: 'selection', scope, selection }), []);
    const beginNavigation = useCallback(() => dispatch({ type: 'navigate' }), []);
    useEffect(() => { try {
        localStorage.setItem(FAVORITES_KEY, JSON.stringify(state.favorites));
    }
    catch { /* optional storage */ } }, [state.favorites]);
    useEffect(() => {
        const sync = (event: StorageEvent) => { if (event.key === FAVORITES_KEY || event.key === null)
            dispatch({ type: 'favorites', update: readFavorites().favorites }); };
        window.addEventListener('storage', sync);
        return () => window.removeEventListener('storage', sync);
    }, []);
    return <Context.Provider value={{ ...state, primary: primaryFavorite(state.favorites), setFavorites, beginNavigation, remember }}>{children}</Context.Provider>;
}
export const useFavoriteDefaults = () => useContext(Context);
// One policy for school, game and perspective controls. Explicit empty selections mean "all"/"none".
export function useFavoriteSelection({ scope, eligible, fallback = '', initial = '', preferred, allowQuery = false }: {
    scope: string;
    eligible: readonly string[];
    fallback?: string;
    initial?: string;
    preferred?: string | ((primary: string | null) => string);
    allowQuery?: boolean;
}) {
    const { primary, navigation, changedAt, selections, remember } = useFavoriteDefaults();
    const [selection, setSelection] = useState<DefaultSelection>(() => initial ? { value: initial, primary } : selections[scope] ?? { value: null, primary });
    const [previousInitial, setPreviousInitial] = useState(initial);
    useEffect(() => { if (initial !== previousInitial) {
        setPreviousInitial(initial);
        const next = { value: initial || null, primary };
        setSelection(next);
        remember(scope, next);
    } }, [initial, previousInitial, primary, remember, scope]);
    const rebase = selection.primary !== primary && navigation > changedAt;
    useEffect(() => { if (rebase) {
        const next = { value: null, primary };
        setSelection(next);
        remember(scope, next);
    } }, [rebase, primary, remember, scope]);
    const value = resolveFavoriteSelection(selection, primary, navigation, changedAt, eligible, fallback, typeof preferred === 'function' ? preferred(rebase ? primary : selection.primary) : preferred, allowQuery);
    const choose = useCallback((next: SetStateAction<string>) => { const entry = { value: typeof next === 'function' ? next(value) : next, primary }; setSelection(entry); remember(scope, entry); }, [primary, value, scope, remember]);
    return [value, choose] as const;
}
