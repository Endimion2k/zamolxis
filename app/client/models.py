"""Modele de date pentru un dosar returnat de web service-ul portal.just.ro.

Numele câmpurilor urmează WSDL-ul real (vezi PLAN.md §3), traduse în snake_case.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Parte:
    """O parte într-un dosar (reclamant, pârât, intervenient etc.)."""

    nume: str
    calitate: str  # ECRIS: calitateParte (ex. "Reclamant", "Pârât", "Intervenient")


@dataclass(slots=True)
class Sedinta:
    """Un termen / o ședință de judecată."""

    data: str  # ISO datetime, așa cum vine din serviciu
    ora: str
    solutie: str
    solutie_sumar: str
    complet: str
    numar_document: str


@dataclass(slots=True)
class Dosar:
    """Un dosar (caz) de pe portalul instanțelor."""

    numar: str  # număr unic ECRIS (ex. "1234/3/2024")
    numar_vechi: str
    data: str  # data înregistrării (ISO datetime)
    institutie: str  # cod instanță (ex. "TribunalulBUCURESTI")
    departament: str
    categorie: str  # categorieCazNume (ex. "Litigii cu profesioniștii")
    stadiu: str  # stadiuProcesualNume (ex. "Fond", "Apel")
    obiect: str  # text liber — semnalul principal pentru clasificare
    data_modificare: str
    parti: list[Parte] = field(default_factory=list)
    sedinte: list[Sedinta] = field(default_factory=list)

    @property
    def numar_parti(self) -> int:
        return len(self.parti)

    def parti_cu_calitate(self, calitate: str) -> list[Parte]:
        """Părțile cu o anumită calitate (case-insensitive, match parțial)."""
        c = calitate.lower()
        return [p for p in self.parti if c in (p.calitate or "").lower()]
