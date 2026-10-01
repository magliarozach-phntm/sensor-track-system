import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import SessionLocal, get_db
from app.models.demo import DemoState
from app.services.time_utils import ensure_utc

router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger(__name__)
DAILY_LIMIT = 12
DURATION = 60
COOLDOWN = 300
tasks: set[asyncio.Task] = set()


def describe(state: DemoState, now: datetime) -> dict:
    running = state.running_until and ensure_utc(state.running_until) > now
    next_at = state.next_allowed_at
    if state.run_day == now.date() and state.runs >= DAILY_LIMIT:
        next_at = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), timezone.utc)
    return {
        "running": bool(running),
        "ends_at": ensure_utc(state.running_until).isoformat() if running else None,
        "next_allowed_at": ensure_utc(next_at).isoformat() if next_at else None,
        "runs_remaining": max(0, DAILY_LIMIT - state.runs) if state.run_day == now.date() else DAILY_LIMIT,
        "error": state.error,
        "server_time": now.isoformat(),
    }


def read_state(db: Session, lock: bool = False) -> DemoState:
    stmt = select(DemoState).where(DemoState.id == 1)
    state = db.scalar(stmt.with_for_update() if lock else stmt)
    if state is None:
        raise HTTPException(503, "Demo setup is not complete")
    return state


@router.get("")
def demo_status(db: Session = Depends(get_db)):
    return describe(read_state(db), datetime.now(timezone.utc))


def finish(error: str | None):
    with SessionLocal() as db:
        state = read_state(db, lock=True)
        state.running_until = None
        state.error = error
        db.commit()


async def run_demo():
    process = None
    error = None
    try:
        env = dict(os.environ)
        # Fixed loopback destination; visitors cannot choose a target or arguments.
        env["SENSOR_API_URL"] = f"http://127.0.0.1:{os.getenv('PORT', '8000')}"
        env["SENSOR_API_KEY"] = settings.sensor_api_key
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(Path(__file__).resolve().parents[2] / "simulator/sensor_simulator.py"),
            "--cycles", "30", "--max-tracks", "3",
            env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            code = await asyncio.wait_for(process.wait(), timeout=DURATION)
            if code:
                error = "The demo could not finish. Please try again after the cooldown."
        except TimeoutError:
            pass  # The public demo always stops after one minute.
    except asyncio.CancelledError:
        error = "The demo stopped during an application restart."
        raise
    except Exception:
        logger.exception("Public demo failed")
        error = "The demo could not start. Please try again after the cooldown."
    finally:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        try:
            await asyncio.to_thread(finish, error)
        except Exception:
            logger.exception("Could not update demo completion state")


@router.post("", status_code=202)
async def start_demo(db: Session = Depends(get_db)):
    if settings.app_env == "production" and not settings.sensor_api_key:
        raise HTTPException(503, "Demo ingestion is not configured")
    now = datetime.now(timezone.utc)
    state = read_state(db, lock=True)
    status = describe(state, now)
    if status["running"] or (status["next_allowed_at"] and datetime.fromisoformat(status["next_allowed_at"]) > now):
        db.rollback()
        raise HTTPException(429, detail=status)
    if state.run_day != now.date():
        state.run_day, state.runs = now.date(), 0
    state.runs += 1
    state.running_until = now + timedelta(seconds=DURATION)
    state.next_allowed_at = now + timedelta(seconds=DURATION + COOLDOWN)
    state.error = None
    db.commit()
    task = asyncio.create_task(run_demo())
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return describe(state, now)


async def stop_demos():
    pending = list(tasks)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
