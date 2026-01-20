
from src.booking.router import router as booking_router
from src.machine.router import router as machine_router
from src.user.router import router as user_router


def register_routers(app):
    """Register all routers with the FastAPI app"""
    app.include_router(user_router)
    app.include_router(booking_router)
    app.include_router(machine_router)
