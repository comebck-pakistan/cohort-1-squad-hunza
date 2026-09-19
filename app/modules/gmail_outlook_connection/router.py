from fastapi import APIRouter,Depends
from app.core.deps import get_current_user

router=APIRouter(prefix="/allconnections",tags=['allconnections'])


@router.get("/all-status")
async def all_connections_status(current_user: dict = Depends(get_current_user)):
    from app.modules.gmail_integration import repository as gmail_repo
    from app.modules.outlook_integration import repository as outlook_repo
    
    gmail_connections = gmail_repo.list_connections_for_user(current_user["id"])
    outlook_connections = outlook_repo.list_connections_for_user(current_user["id"])
    
    return gmail_connections + outlook_connections