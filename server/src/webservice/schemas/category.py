from pydantic import BaseModel

# Category-related Pydantic models

class CategoryResponse(BaseModel):
    categories: list[dict]  # Tree structure can be complex, using dict for flexibility
    categoryIDs: list[str]  # List of category IDs

class CategoryPathsResponse(BaseModel):
    paths: list[str]  # List of category paths 