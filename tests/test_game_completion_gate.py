from datetime import datetime, timezone

from cfb_analytics.game_completion_gate import should_refresh


def snapshot(completed=False):
    return {"season": 2026, "games": [
        {"game_id": 42, "completed": completed, "start_date": "2026-11-07T19:00:00Z"}
    ]}


def raw(completed):
    return [{"id": 42, "season": 2026, "week": 11,
             "homeTeam": "A", "awayTeam": "B", "completed": completed,
             "homePoints": 20 if completed else None,
             "awayPoints": 17 if completed else None}]


NOW = datetime(2026, 11, 8, 4, 0, tzinfo=timezone.utc)


def test_new_final_triggers_refresh():
    assert should_refresh("schedule", "*/15 0-6 * 8-12 *", snapshot(), raw(True), NOW)[0]


def test_no_new_final_skips_refresh():
    assert not should_refresh("schedule", "*/15 0-6 * 8-12 *", snapshot(), raw(False), NOW)[0]


def test_already_completed_does_not_republish():
    assert not should_refresh("schedule", "*/15 0-6 * 8-12 *", snapshot(True), raw(True), NOW)[0]


def test_daily_and_manual_still_run():
    assert should_refresh("schedule", "23 11 * * *", snapshot(), [], NOW)[0]
    assert should_refresh("workflow_dispatch", "", snapshot(), [], NOW)[0]


def test_old_pending_game_skips_poll():
    assert not should_refresh("schedule", "*/15 0-6 * 8-12 *", snapshot(), [], datetime(2026, 11, 12, tzinfo=timezone.utc))[0]
