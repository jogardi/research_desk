from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.routing import APIRouter
from threading import Lock
from shared.logger import Logger
import json
import asyncio
import threading

# Import existing authentication system
from webservice.session_manager import SessionManager

# Simple global state for small user base
connections = {}  # websocket_id -> websocket
stop_flags = {}   # websocket_id -> boolean
stop_flags_lock = Lock()

websocket_router = APIRouter()

async def authenticate_websocket_connection(websocket: WebSocket) -> tuple[bool, str]:
    """Authenticate WebSocket connection and return (success, kb_name)."""
    token = websocket.query_params.get("token") if websocket.query_params else None
    
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Authentication token required")
        
        class TokenCredentials: 
            def __init__(self, token: str): self.credentials = token
        
        session_data = SessionManager._validate_session(TokenCredentials(token))
        kb_name = session_data['kb_name']
        Logger.info(f'Authenticated WebSocket connection for kb_name: {kb_name}')
        return True, kb_name
    except HTTPException as e:
        # Send auth error message before closing
        await websocket.accept()
        await websocket.send_json({"type": "auth_error", "data": f"Authentication failed: {e.detail}"})
        await websocket.close(code=1008, reason=f"Authentication failed: {e.detail}")
        return False, None

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Require authentication for all WebSocket connections
    auth_success, kb_name = await authenticate_websocket_connection(websocket)
    if not auth_success:
        return  # Authentication failed, connection closed
    
    await websocket.accept()
    client_id = id(websocket)
    
    # Register client
    connections[client_id] = websocket
    with stop_flags_lock:
        stop_flags[client_id] = False
    print(f'Client connected: {client_id} with kb_name: {kb_name}')
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Only add JSON validation (essential for stability)
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": "Invalid JSON"})
                continue
            
            if message.get("type") == "stop_stream":
                with stop_flags_lock:
                    stop_flags[client_id] = True
                await websocket.send_json({"type": "done", "data": "stopped"})
                
            elif message.get("type") == "stream_chat":
                # Parse message data like Flask version did with json.loads(message)
                message_data = message.get("data")
                if isinstance(message_data, str):
                    try:
                        message_data = json.loads(message_data)
                    except json.JSONDecodeError:
                        await websocket.send_json({"type": "error", "data": "Invalid message data format"})
                        continue
                await handle_stream_chat(client_id, websocket, message_data, kb_name)
                
    except WebSocketDisconnect:
        cleanup_client(client_id)
    except Exception as e:
        print(f"Error: {e}")
        cleanup_client(client_id)

def cleanup_client(client_id):
    connections.pop(client_id, None)
    with stop_flags_lock:
        stop_flags.pop(client_id, None)
    print(f'Client disconnected: {client_id}')

async def handle_stream_chat(client_id, websocket, message_data, kb_name):
    print(f'Received message from {client_id}: {message_data} (kb_name: {kb_name})')
    
    # Reset stop flag at the start of a new stream
    with stop_flags_lock:
        stop_flags[client_id] = False
    
    # Get the current event loop to pass to the thread
    loop = asyncio.get_running_loop()
    
    # Simple threading for agent
    def run_agent():
        from webservice.llm import agent
        
        # Create a proper emit function that sends messages to WebSocket
        def sync_emit(event_type, data):
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": event_type, "data": data}),
                loop
            )
        
        try:
            for chunk in agent.stream_chat(message_data, kb_name, sync_emit):
                with stop_flags_lock:
                    if stop_flags.get(client_id, True):
                        print(f'Stream aborted for {client_id}')
                        # Send stop notification like Flask version
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json({"type": "done", "data": "stopped"}),
                            loop
                        )
                        return
                # Send chunk back to client
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "stream_chat_response", "data": chunk}),
                    loop
                )
            # Send completion message
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "done", "data": "done"}),
                loop
            )
        except Exception as e:
            error_message = f"Chat processing error: {str(e)}"
            print(f"Error in agent processing: {error_message}")
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "error", "data": error_message}),
                loop
            )
    
    # Run in daemon thread - this prevents semaphore leaks on shutdown
    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()

def init_fastapi_websockets(app):
    """Initialize FastAPI WebSockets with the given FastAPI app"""
    app.include_router(websocket_router)
    Logger.info("FastAPI WebSockets initialized") 