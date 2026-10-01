import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.demo import DemoState
from app.routes import demo


@pytest.fixture
def demo_state(db_session, monkeypatch):
    state = DemoState(id=1, runs=0)
    db_session.add(state)
    db_session.commit()
    monkeypatch.setattr(demo, "run_demo", AsyncMock())
    return state


def test_start_and_shared_cooldown(client, demo_state, db_session):
    assert client.get('/demo').json()['runs_remaining'] == 12
    started = client.post('/demo')
    assert started.status_code == 202
    assert started.json()['running']
    assert started.json()['runs_remaining'] == 11
    assert client.post('/demo').status_code == 429
    demo_state.running_until = None
    db_session.commit()
    # Completion or process restart does not discard the persisted cooldown.
    assert client.post('/demo').status_code == 429
    assert client.get('/demo').json()['running'] is False


def test_daily_limit_and_next_day(client, demo_state, db_session):
    demo_state.run_day = datetime.now(timezone.utc).date()
    demo_state.runs = 12
    db_session.commit()
    response = client.post('/demo')
    assert response.status_code == 429
    assert response.json()['detail']['runs_remaining'] == 0
    demo_state.run_day -= timedelta(days=1)
    db_session.commit()
    assert client.post('/demo').status_code == 202
    assert demo_state.runs == 1


def test_expired_run_after_crash_can_recover(client, demo_state, db_session):
    demo_state.running_until = datetime.now(timezone.utc) - timedelta(minutes=10)
    demo_state.next_allowed_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()
    assert client.post('/demo').status_code == 202


def test_missing_migration_fails_closed(client):
    assert client.post('/demo').status_code == 503


def test_runner_kills_process_at_deadline(monkeypatch):
    process = AsyncMock()
    process.returncode = None
    process.wait.side_effect = [TimeoutError(), 0]
    from unittest.mock import Mock
    process.kill = Mock()
    spawn = AsyncMock(return_value=process)
    finish = Mock()
    monkeypatch.setattr(demo.asyncio, 'create_subprocess_exec', spawn)
    monkeypatch.setattr(demo, 'finish', finish)
    asyncio.run(demo.run_demo())
    process.kill.assert_called_once()
    finish.assert_called_once_with(None)
    assert spawn.call_args.args[-4:] == ('--cycles', '30', '--max-tracks', '3')
    assert spawn.call_args.kwargs['env']['SENSOR_API_URL'].startswith('http://127.0.0.1:')


def test_spawn_failure_is_reported_without_leaking_details(monkeypatch):
    from unittest.mock import Mock
    monkeypatch.setattr(demo.asyncio, 'create_subprocess_exec', AsyncMock(side_effect=OSError('private detail')))
    finish = Mock()
    monkeypatch.setattr(demo, 'finish', finish)
    asyncio.run(demo.run_demo())
    assert 'could not start' in finish.call_args.args[0]
    assert 'private detail' not in finish.call_args.args[0]
