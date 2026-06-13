"""Detectarea „valurilor" de litigii — dosare individuale identice agregate
după (pârât, tip de obiect). Complementar acțiunilor colective clasice."""

from .analyzer import descopera_valuri, scaneaza_grupuri
from .bucket import bucket_obiect

__all__ = ["scaneaza_grupuri", "descopera_valuri", "bucket_obiect"]
