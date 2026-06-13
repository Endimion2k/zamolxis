"""Client pentru web service-ul portal.just.ro (CautareDosare / CautareSedinte)."""

from .models import Dosar, Parte, Sedinta
from .soap import PortalClient, PortalError

__all__ = ["Dosar", "Parte", "Sedinta", "PortalClient", "PortalError"]
