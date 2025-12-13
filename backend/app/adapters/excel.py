"""Excel file adapter."""

import io
from typing import Any, Optional
import pandas as pd
from datetime import date

from app.adapters.base import FileAdapter
from app.models.budget import (
    BudgetIndicators,
    LigneBudget,
    Depense,
    CategorieDepense,
)
from app.models.edt import (
    EDTIndicators,
    ChargeEnseignant,
    OccupationSalle,
    TypeCours,
)


class ExcelAdapter(FileAdapter[BudgetIndicators]):
    """
    Adapter for Excel files.
    Handles budget, EDT, and other Excel-based data sources.
    """
    
    @property
    def source_name(self) -> str:
        return "Excel"
    
    async def fetch_raw(self, **kwargs) -> Any:
        """Not used for file adapters - use parse_file instead."""
        return {}
    
    def transform(self, raw_data: Any) -> BudgetIndicators:
        """Transform parsed Excel data to indicators."""
        return raw_data
    
    def parse_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse Excel file to DataFrame."""
        return pd.read_excel(io.BytesIO(file_content))
    
    def parse_budget_file(self, file_content: bytes) -> BudgetIndicators:
        """
        Parse budget Excel file.
        
        Expected columns:
        - Catégorie
        - Budget Initial
        - Budget Modifié
        - Engagé
        - Payé
        """
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        lignes = []
        total_initial = 0
        total_engage = 0
        total_paye = 0
        
        for _, row in df.iterrows():
            cat_str = str(row.get("catégorie", row.get("categorie", "autre"))).lower()
            
            # Map to enum
            cat_map = {
                "fonctionnement": CategorieDepense.FONCTIONNEMENT,
                "investissement": CategorieDepense.INVESTISSEMENT,
                "missions": CategorieDepense.MISSIONS,
                "fournitures": CategorieDepense.FOURNITURES,
                "maintenance": CategorieDepense.MAINTENANCE,
                "formation": CategorieDepense.FORMATION,
            }
            categorie = cat_map.get(cat_str, CategorieDepense.AUTRE)
            
            budget_initial = float(row.get("budget initial", row.get("budget_initial", 0)) or 0)
            budget_modifie = float(row.get("budget modifié", row.get("budget_modifie", budget_initial)) or budget_initial)
            engage = float(row.get("engagé", row.get("engage", 0)) or 0)
            paye = float(row.get("payé", row.get("paye", 0)) or 0)
            disponible = budget_modifie - engage
            
            lignes.append(LigneBudget(
                categorie=categorie,
                budget_initial=budget_initial,
                budget_modifie=budget_modifie,
                engage=engage,
                paye=paye,
                disponible=disponible,
            ))
            
            total_initial += budget_initial
            total_engage += engage
            total_paye += paye
        
        total_disponible = total_initial - total_engage
        
        return BudgetIndicators(
            annee=date.today().year,
            budget_total=total_initial,
            total_engage=total_engage,
            total_paye=total_paye,
            total_disponible=total_disponible,
            taux_execution=total_paye / total_initial if total_initial > 0 else 0,
            taux_engagement=total_engage / total_initial if total_initial > 0 else 0,
            par_categorie=lignes,
            evolution_mensuelle={},
            top_depenses=[],
            previsionnel=total_initial,
            realise=total_paye,
        )
    
    def parse_edt_file(self, file_content: bytes) -> EDTIndicators:
        """
        Parse EDT Excel file.
        
        Expected columns:
        - Enseignant
        - Module
        - Type (CM/TD/TP)
        - Heures
        - Salle (optional)
        """
        df = pd.read_excel(io.BytesIO(file_content))
        df.columns = df.columns.str.lower().str.strip()
        
        # Calculate per teacher
        charges: dict[str, ChargeEnseignant] = {}
        heures_par_module: dict[str, float] = {}
        salles: dict[str, float] = {}
        
        total_cm = 0
        total_td = 0
        total_tp = 0
        
        for _, row in df.iterrows():
            enseignant = str(row.get("enseignant", "Inconnu"))
            module = str(row.get("module", ""))
            type_cours = str(row.get("type", "TD")).upper()
            heures = float(row.get("heures", 0) or 0)
            salle = str(row.get("salle", ""))
            
            # Update teacher charges
            if enseignant not in charges:
                charges[enseignant] = ChargeEnseignant(
                    enseignant=enseignant,
                    heures_cm=0, heures_td=0, heures_tp=0, heures_projet=0,
                    total_heures=0, heures_statutaires=192, heures_complementaires=0
                )
            
            charge = charges[enseignant]
            if type_cours == "CM":
                charge.heures_cm += heures
                total_cm += heures
            elif type_cours == "TD":
                charge.heures_td += heures
                total_td += heures
            elif type_cours == "TP":
                charge.heures_tp += heures
                total_tp += heures
            else:
                charge.heures_projet += heures
            
            charge.total_heures = (
                charge.heures_cm * 1.5 +  # CM compte 1.5x
                charge.heures_td +
                charge.heures_tp +
                charge.heures_projet
            )
            charge.heures_complementaires = max(0, charge.total_heures - charge.heures_statutaires)
            
            # Update module hours
            heures_par_module[module] = heures_par_module.get(module, 0) + heures
            
            # Update room occupation
            if salle:
                salles[salle] = salles.get(salle, 0) + heures
        
        # Build room occupation list
        occupation_salles = [
            OccupationSalle(
                salle=salle,
                capacite=30,  # Default capacity
                heures_occupees=heures,
                heures_disponibles=40 * 35,  # 40h/week * 35 weeks
                taux_occupation=heures / (40 * 35),
            )
            for salle, heures in salles.items()
        ]
        
        total_heures = total_cm + total_td + total_tp
        total_hc = sum(c.heures_complementaires for c in charges.values())
        
        return EDTIndicators(
            periode_debut=date(date.today().year, 9, 1),
            periode_fin=date(date.today().year + 1, 6, 30),
            total_heures=total_heures,
            heures_cm=total_cm,
            heures_td=total_td,
            heures_tp=total_tp,
            repartition_types={
                "CM": total_cm,
                "TD": total_td,
                "TP": total_tp,
            },
            charges_enseignants=list(charges.values()),
            total_heures_complementaires=total_hc,
            occupation_salles=occupation_salles,
            taux_occupation_moyen=sum(s.taux_occupation for s in occupation_salles) / len(occupation_salles) if occupation_salles else 0,
            heures_par_module=heures_par_module,
            evolution_hebdo={},
        )


# Mock Excel adapter for development
class MockExcelAdapter(FileAdapter[BudgetIndicators]):
    """Mock Excel adapter with sample data."""
    
    @property
    def source_name(self) -> str:
        return "Excel (Mock)"
    
    async def fetch_raw(self, **kwargs) -> Any:
        return {}
    
    def transform(self, raw_data: Any) -> BudgetIndicators:
        return self.get_mock_budget()
    
    def parse_file(self, file_content: bytes, filename: str) -> Any:
        return {}
    
    def get_mock_budget(self) -> BudgetIndicators:
        """Return mock budget data."""
        return BudgetIndicators(
            annee=2024,
            budget_total=150000,
            total_engage=95000,
            total_paye=72000,
            total_disponible=55000,
            taux_execution=0.48,
            taux_engagement=0.63,
            par_categorie=[
                LigneBudget(
                    categorie=CategorieDepense.FONCTIONNEMENT,
                    budget_initial=80000, budget_modifie=82000,
                    engage=55000, paye=45000, disponible=27000
                ),
                LigneBudget(
                    categorie=CategorieDepense.INVESTISSEMENT,
                    budget_initial=50000, budget_modifie=48000,
                    engage=30000, paye=20000, disponible=18000
                ),
                # LigneBudget(
                #     categorie=CategorieDepense.MISSIONS,
                #     budget_initial=20000, budget_modifie=20000,
                #     engage=10000, paye=7000, disponible=10000
                # ),
            ],
            evolution_mensuelle={
                "2024-09": 8000, "2024-10": 12000, "2024-11": 15000,
                "2024-12": 10000, "2025-01": 8000, "2025-02": 9000,
            },
            top_depenses=[
                Depense(id="1", libelle="Serveur Dell", montant=15000,
                       categorie=CategorieDepense.INVESTISSEMENT, date=date(2024, 10, 15)),
                Depense(id="2", libelle="Licences VMware", montant=8000,
                       categorie=CategorieDepense.FONCTIONNEMENT, date=date(2024, 9, 1)),
            ],
            previsionnel=150000,
            realise=72000,
        )
    
    def get_mock_edt(self) -> EDTIndicators:
        """Return mock EDT data."""
        return EDTIndicators(
            periode_debut=date(2024, 9, 1),
            periode_fin=date(2025, 6, 30),
            total_heures=2500,
            heures_cm=400,
            heures_td=1200,
            heures_tp=900,
            repartition_types={"CM": 400, "TD": 1200, "TP": 900},
            charges_enseignants=[
                ChargeEnseignant(
                    enseignant="Dupont Jean",
                    heures_cm=60, heures_td=100, heures_tp=40, heures_projet=20,
                    total_heures=250, heures_statutaires=192, heures_complementaires=58
                ),
                ChargeEnseignant(
                    enseignant="Martin Sophie",
                    heures_cm=40, heures_td=120, heures_tp=50, heures_projet=10,
                    total_heures=240, heures_statutaires=192, heures_complementaires=48
                ),
            ],
            total_heures_complementaires=320,
            occupation_salles=[
                OccupationSalle(salle="A101", capacite=30, heures_occupees=800,
                               heures_disponibles=1400, taux_occupation=0.57),
                OccupationSalle(salle="B202", capacite=24, heures_occupees=650,
                               heures_disponibles=1400, taux_occupation=0.46),
            ],
            taux_occupation_moyen=0.52,
            heures_par_module={"R101": 120, "R102": 100, "R103": 80},
            evolution_hebdo={},
        )
