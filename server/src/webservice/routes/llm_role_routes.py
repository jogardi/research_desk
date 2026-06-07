import json
from fastapi import APIRouter, HTTPException, Depends
from webservice.persistence.research_desk_llm_role_sqlite import ResearchDeskLLMRoleSqlite
from webservice.session_manager import protected_user_id, protected, protected_user_kb_name
from webservice.schemas.llm_role import CreateLLMRoleRequest, LLMRoleItem
from webservice.schemas.common import MessageResponse


# FastAPI Router for all LLM role routes
router = APIRouter(tags=["llm_roles"])

#
# LLM Role routes
#
@router.post("/api/llm-roles", response_model=LLMRoleItem)
def create_llm_role(
    request: CreateLLMRoleRequest, 
        user_id: str = Depends(protected_user_id), 
        kb_name: str = Depends(protected_user_kb_name)):
    """Create a new LLM role."""
    
    db = ResearchDeskLLMRoleSqlite()
    
    role, error, status_code = db.create_role(request.role, user_id, kb_name)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    
    return LLMRoleItem(id=role['id'], role=role['role'], ownerId=role['owner_id'])

@router.delete("/api/llm-roles/{role_id}", response_model=MessageResponse)
def delete_llm_role(
    role_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Delete an LLM role with the given role_id."""
    db = ResearchDeskLLMRoleSqlite()
    error, status_code = db.delete_role(role_id, kb_name)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    return MessageResponse(message="LLM role deleted.")

@router.get("/api/llm-roles/list", response_model=list[LLMRoleItem])
def get_llm_role_list(user_id: str = Depends(protected_user_id), kb_name: str = Depends(protected_user_kb_name)):
    """Get the LLM role list."""
    db = ResearchDeskLLMRoleSqlite()
    roles, error, status_code = db.get_roles(user_id, kb_name)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    
    role_list_items = [
        LLMRoleItem(id=role["id"], role=role['role'], ownerId=role["owner_id"]) 
        for role in roles
    ]
    return role_list_items

@router.put("/api/llm-roles", response_model=MessageResponse)
def update_llm_role(
    request: LLMRoleItem, kb_name: str = Depends(protected_user_kb_name)):
    """Update an LLM role with the given role_id."""
    db = ResearchDeskLLMRoleSqlite()
    
    error, status_code = db.update_role(request.id, request.role, kb_name)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    
    return MessageResponse(message="LLM role updated.")

@router.get("/api/llm-roles/{role_id}", response_model=LLMRoleItem)
def get_llm_role_detail(
    role_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get the LLM role detail with the given role_id."""
    db = ResearchDeskLLMRoleSqlite()
    role, error, status_code = db.get_role(role_id, kb_name)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    
    return LLMRoleItem(id=role['id'], role=role['role'], ownerId=role['owner_id']
    )
