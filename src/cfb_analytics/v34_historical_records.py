"""Historical completed-season win records from canonical CFBD games.

FBS-FCS games count toward FBS teams' actual wins. The season is only
accepted when the caller explicitly identifies it as complete.
"""
from .ingestion import normalize_cfbd_games
from .v34_season_records import season_records


def historical_season_records(raw_by_season, *, fbs_teams_by_season, completed_seasons):
    output = []
    for season, raw in sorted(raw_by_season.items()):
        if season not in completed_seasons:
            continue
        if season not in fbs_teams_by_season:
            raise ValueError(f"Missing FBS classification for {season}")
        if not isinstance(raw, list) or not raw:
            raise ValueError(f"Missing games for {season}")
        games = normalize_cfbd_games(raw, season)
        # A completed historical season may retain cancelled fixtures.
        # Never count unplayed games as wins or losses.
        games = [game for game in games if game.completed]
        if not games:
            raise ValueError(f"No completed games for {season}")
        records = season_records(games, eligible_teams=fbs_teams_by_season[season])
        output.extend(records)
    return output
