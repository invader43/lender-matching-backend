"""Router initialization."""

from .parameters import router as parameters_router
from .lenders import router as lenders_router
from .policies import router as policies_router
from .applications import router as applications_router

__all__ = [
    "parameters_router",
    "lenders_router",
    "policies_router",
    "applications_router",
]
