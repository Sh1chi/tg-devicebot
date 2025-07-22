from .start import router as start_router
from .catalog_wizard import router as catalog_router
from .broadcast import router as broadcast_router

# Список всех маршрутизаторов, которые будут подключены в main.py
routers = (
    start_router,
    catalog_router,
    broadcast_router
)
