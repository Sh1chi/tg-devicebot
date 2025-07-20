from .start import router as start_router
from .catalog import router as catalog_router
from .admin import router as admin_router

routers = (start_router, catalog_router, admin_router)
