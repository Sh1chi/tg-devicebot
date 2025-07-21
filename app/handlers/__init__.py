from .start import router as start_router
from .catalog_wizard import router as catalog_router
from .admin import router as admin_router
from .broadcast import router as broadcast_router

routers = (
    start_router,
    catalog_router,
    broadcast_router,
    admin_router)
