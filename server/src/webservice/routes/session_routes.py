import json

from fastapi import APIRouter, HTTPException, Depends

from shared.logger import Logger
from webservice.session_manager import protected_user_id, protected_user_kb_name
from webservice.schemas.session import (
    CreateSessionRequest, CreateSessionResponse, UpdateSessionRequest, 
    DeleteSessionResponse, UpdateSessionResponse, SessionItem
)

from webservice.persistence.research_desk_session_sqlite import ResearchDeskSessionSqlite

# FastAPI Router for all session routes
router = APIRouter(tags=["sessions"])

#
# Session routes
#
@router.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest, 
                   user_id: str = Depends(protected_user_id),
                   kb_name: str = Depends(protected_user_kb_name)):
    """Create a new session."""
    print(f"*** create_session: {user_id}")

    from webservice.models import defaultModel, models # Temporary until moved to database table

    session_detail = {
        'id': '',
        'name': request.name,
        'kb_name': kb_name,
        'categories': [],
        'vectorDB': 'hnswlib',
        'topK': 25,
        'minSimilarityScore': 0.0,
        'query': '',
        'chunks': [],
        'summary': '',
        'notes': '',
        'systemPrompt': 1, 
        'temperature': 1,   
        "maxTokens": 1000,
        "model": defaultModel, 
        'chats': {
            defaultModel['value']: [] 
        }
    }
    detail_str = json.dumps(session_detail)
    
    try: 
        session_id = ResearchDeskSessionSqlite.create_session(request.name, 
                            request.description, detail_str, user_id, kb_name)
    except Exception as e:
        Logger.error("Cannot create session", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Cannot create session")
    
    session_detail['id'] = session_id
    detail_str = json.dumps(session_detail)
    
    try:
        # update the session with the embedded session id gotten from the create
        ResearchDeskSessionSqlite.update_session(session_id, request.name, 
                                        request.description, detail_str, user_id, kb_name)
    except Exception as e:
        Logger.error("Cannot create session", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Cannot create session")
 
    session_item = SessionItem(id=session_id, name=request.name, description=request.description)
    
    return CreateSessionResponse(sessionItem=session_item, sessionDetail=session_detail)

@router.delete("/api/sessions/{session_id}", response_model=DeleteSessionResponse)
def delete_session(session_id: str, user_id: str = Depends(protected_user_id),
                   kb_name: str = Depends(protected_user_kb_name)):
    """Delete a session."""
    try:
        ResearchDeskSessionSqlite.delete_session(session_id, user_id, kb_name)
    except Exception as e:
        Logger.error("Cannot delete session", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Cannot delete session")
   
    return DeleteSessionResponse(message="Session deleted.")

@router.get("/api/sessions/list", response_model=list[dict])
def get_session_list(user_id: str = Depends(protected_user_id),
                     kb_name: str = Depends(protected_user_kb_name)):
    """
    Get list of sessions for the current user.
    """
    print(f"*** getting session list for the user {user_id} and the specific kb_name {kb_name}")
    try:
        sessions = ResearchDeskSessionSqlite.get_sessions(user_id, kb_name)
        return sessions
    except Exception as e:
        Logger.error("Cannot get session", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get sessions.")

@router.put("/api/sessions/{session_id}", response_model=UpdateSessionResponse)
def update_session(session_id: str, request: UpdateSessionRequest, 
                   user_id: str = Depends(protected_user_id),
                   kb_name: str = Depends(protected_user_kb_name)):
    """Update a session."""
    detail_str = json.dumps(request.detail)
    
    try:
        ResearchDeskSessionSqlite.update_session(session_id, request.name, 
                                    request.description, detail_str, user_id, kb_name)
    except Exception as e:
        Logger.error("Cannot update session", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to update session.")
    
    return UpdateSessionResponse(message="Session updated.")

@router.get("/api/sessions/detail/{session_id}")
def get_session_detail(session_id: str, user_id: str = Depends(protected_user_id),
                       kb_name: str = Depends(protected_user_kb_name)):
    """
    Get detailed session data for a specific session.
    """
    try:
        session_json_string = ResearchDeskSessionSqlite.get_session(session_id, user_id, kb_name)
        # Parse the JSON string to return an object instead of a string
        session = json.loads(session_json_string)
        return session
    except Exception as e:
        Logger.error("Cannot get session", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get session.")
    

@router.post("/api/sessions/fork/{session_id}", response_model=CreateSessionResponse)
def fork_session_detail(session_id: str, request: CreateSessionRequest, 
                        user_id: str = Depends(protected_user_id),
                        kb_name: str = Depends(protected_user_kb_name)):
    """Fork an existing session by copying its details and creating a new session with a new name/description."""
    try:
        # Retrieve the original session detail (must use get_session, not get_sessions)
        session_json_string = ResearchDeskSessionSqlite.get_session(session_id, user_id, kb_name)
        session_detail = json.loads(session_json_string)
    except Exception as e:
        Logger.error("Cannot retrieve session to fork", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to retrieve session to fork.")

    # Update the name and description in the detail object
    session_detail['name'] = request.name
    session_detail['description'] = request.description
    session_detail['id'] = ''  # Clear id before creating new session

    detail_str = json.dumps(session_detail)

    try:
        # Insert the new session
        new_session_id = ResearchDeskSessionSqlite.create_session(request.name, 
                                    request.description, detail_str, user_id, kb_name)
    except Exception as e:
        Logger.error("Cannot fork session (create)", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Cannot fork session.")

    # Set the new session id in the detail and update
    session_detail['id'] = new_session_id
    detail_str = json.dumps(session_detail)
    
    try:
        ResearchDeskSessionSqlite.update_session(new_session_id, request.name, 
                                    request.description, detail_str, user_id, kb_name)
    except Exception as e:
        Logger.error("Cannot fork session (update)", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Cannot finalize forked session.")

    session_item = SessionItem(id=new_session_id, name=request.name, description=request.description)
    return CreateSessionResponse(sessionItem=session_item, sessionDetail=session_detail)
    
