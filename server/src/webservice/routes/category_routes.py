from fastapi import APIRouter, HTTPException, Depends, Query
from shared.category_tree import get_category_tree
from shared.logger import Logger
from webservice.schemas.category import CategoryResponse, CategoryPathsResponse
from webservice.session_manager import protected, protected_user_kb_name

# FastAPI Router for all category routes
router = APIRouter(tags=["categories"], dependencies=[Depends(protected)])

#
# Category routes
#
# get the ACTIVE folders for category tree and category IDs 
@router.get("/api/categories/active", response_model=CategoryResponse)
def get_active_categories(kb_name: str = Depends(protected_user_kb_name)):
    """Get the ACTIVE folders for category tree and category IDs."""
    try:
        folders, tree, IDs = get_category_tree('active', kb_name)
        return CategoryResponse(categories=tree, categoryIDs=IDs)
    except Exception as e:
        Logger.error("Failed to get active categories", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to get active categories.")

# get the Document tree - FastAPI version
@router.get("/api/categories/documents", response_model=CategoryResponse)
def get_document_tree(kb_name: str = Depends(protected_user_kb_name)):
    """Get the document tree with categories and category IDs."""
    try:
        folders, tree, IDs = get_category_tree('documents', kb_name)
        return CategoryResponse(categories=tree, categoryIDs=IDs)
    except Exception as e:
        Logger.error("Failed to get document tree", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to get document tree.")

# get ALL the folders for category tree and category IDs 
@router.get("/api/categories/all", response_model=CategoryResponse)
def get_all_categories(kb_name: str = Depends(protected_user_kb_name)):
    """Get ALL the folders for category tree and category IDs."""
    try:
        folders, tree, IDs = get_category_tree('all', kb_name)
        # cache.all_categoriesPaths = folders
        return CategoryResponse(categories=tree, categoryIDs=IDs)
    except Exception as e:
        Logger.error("Failed to get all categories", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to get all categories.")

# get the category paths from given selected category IDs 
@router.get("/api/categories/paths", response_model=CategoryPathsResponse)
def get_categories_paths(
    categoryIDs: str = Query(..., description="Comma-separated list of category IDs"),
    type: str = Query(default="all", description="Type of categories: 'active' or 'all'"),
    kb_name: str = Depends(protected_user_kb_name)
):
    """Get the category paths from given selected category IDs."""
    try:
        category_ids_list = categoryIDs.split(',') if categoryIDs else []
        
        # Get the appropriate category data based on type
        folders, tree, IDs = get_category_tree(type if type == 'active' else 'all', kb_name)
        
        paths = []
        for category_id in category_ids_list:
            for category in folders:
                if category.get('id') == category_id:
                    # Remove the "Root/" prefix if it exists
                    path = category.get('path', '')
                    if path.startswith('Root/'):
                        path = path[5:]  # Remove "Root/" prefix
                    paths.append(path)
                    break
        
        return CategoryPathsResponse(paths=paths)
    except Exception as e:
        Logger.error("Failed to get category paths", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to get category paths.")
