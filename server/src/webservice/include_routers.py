"""
Router configuration module for the Research Desk FastAPI application.
This module centralizes all router includes to keep server_main.py clean.
"""

from fastapi import FastAPI

from webservice.test_routes import router as test_router
from webservice.routes.user_routes import router as user_fastapi_router
from webservice.routes.session_routes import router as session_fastapi_router
from webservice.routes.llm_routes import router as llm_fastapi_router
from webservice.routes.category_routes import router as category_fastapi_router
from webservice.routes.search_routes import router as search_fastapi_router
from webservice.routes.document_routes import router as document_fastapi_router
from webservice.routes.llm_role_routes import router as llm_role_fastapi_routes
from webservice.routes.social_login_routes import router as social_login_fastapi_router
from webservice.routes.vector_routes import router as vector_fastapi_router
from webservice.routes.excerpt_routes import router as excerpt_fastapi_router
from webservice.routes.kb_builder_routes import router as kb_builder_fastapi_router

def include_routers(app: FastAPI) -> None:
    """
    Include all routers in the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    app.include_router(test_router)
    app.include_router(user_fastapi_router)
    app.include_router(session_fastapi_router)
    app.include_router(llm_fastapi_router)
    app.include_router(category_fastapi_router)
    app.include_router(search_fastapi_router)
    app.include_router(document_fastapi_router)
    app.include_router(llm_role_fastapi_routes)
    app.include_router(social_login_fastapi_router)
    app.include_router(vector_fastapi_router)
    app.include_router(excerpt_fastapi_router)
    app.include_router(kb_builder_fastapi_router)