from fastapi import APIRouter, HTTPException, Depends
from webservice.session_manager import protected
from webservice.schemas.kb_builder import KBBuilderResponse
from shared.logger import Logger
import threading
import time

router = APIRouter(tags=["kb_builder"])

kb_builder_got_work = False
kb_builder_status = "Idle"

_kb_builder_work_last_called_ts: float | None = None
_kb_builder_lock = threading.Lock()


def _kb_builder_watchdog_loop() -> None:
    """Detect stale /work polling and flag/log after 20 minutes."""
    global _kb_builder_work_last_called_ts
    global kb_builder_status

    while True:
        # Simple: wake up every 20 minutes and check last call.
        time.sleep(20 * 60)
        with _kb_builder_lock:
            stale = (time.time() - _kb_builder_work_last_called_ts) > (20 * 60)
            if stale:
                kb_builder_status = "Error"
                # Prevent logging every 20 minutes forever.
                _kb_builder_work_last_called_ts = time.time()
                Logger.error(
                    "KB Builder agent has not called /api/kb_builder/work for > 20 minutes.", report=True)


def _update_watchdog() -> None:
    """Record a /work poll and start watchdog on first poll."""
    global _kb_builder_work_last_called_ts

    start_watchdog = False
    # with _kb_builder_lock:
    #     if _kb_builder_work_last_called_ts is None:
    #         start_watchdog = True
    #     _kb_builder_work_last_called_ts = time.time()
        
    if start_watchdog:
        threading.Thread(target=_kb_builder_watchdog_loop, daemon=True).start()


@router.get("/api/kb_builder/work", response_model=KBBuilderResponse)
def get_kb_work():
    """Get the status of the knowledge base builder - called from KB Builder Agent"""
    global kb_builder_got_work
    global kb_builder_status
    _update_watchdog()

    got_work = kb_builder_got_work

    if got_work:
        kb_builder_status = "Working"
        kb_builder_got_work = False
    return KBBuilderResponse(status=got_work)

@router.get("/api/kb_builder/status", response_model=KBBuilderResponse)
def get_kb_status(_: None = Depends(protected)):  
    """Get the status of the knowledge base builder - called from the frontend"""
    return KBBuilderResponse(status=kb_builder_status)


@router.post("/api/kb_builder/start", response_model=KBBuilderResponse)
def start_kb(_: None = Depends(protected)):
    """Start the knowledge base builder - called from the frontend"""
    global kb_builder_status
    global kb_builder_got_work
    kb_builder_status = "Pending"
    kb_builder_got_work = True
    Logger.error("KB Refresh started.", report=True)
    return KBBuilderResponse(status=kb_builder_status)

@router.post("/api/kb_builder/done", response_model=KBBuilderResponse)
def stop_kb():
    """Stop the knowledge base builder - called from KB Builder Agent"""
    global kb_builder_status
    kb_builder_status = "Idle"
    return KBBuilderResponse(status=kb_builder_status)

@router.post("/api/kb_builder/error", response_model=KBBuilderResponse)
def error_kb():
    """Error the knowledge base builder - called from KB Builder Agent"""
    global kb_builder_status
    kb_builder_status = "Error"
    return KBBuilderResponse(status=kb_builder_status)