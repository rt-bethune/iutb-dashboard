"""Parcoursup CSV file adapter."""

import io
from typing import Any
import pandas as pd
from datetime import date

from app.adapters.base import FileAdapter
from app.models.recrutement import (
    RecrutementIndicators,
    Candidat,
    VoeuStats,
    LyceeStats,
)


class ParcoursupAdapter(FileAdapter[RecrutementIndicators]):
    """
    Adapter for Parcoursup CSV exports.
    
    Parcoursup provides CSV exports with candidate data.
    Format varies by year but typically includes:
    - Candidate info (anonymized)
    - Bac type and mention
    - Geographic origin
    - Application status
    """
    
    @property
    def source_name(self) -> str:
        return "Parcoursup"
    
    async def fetch_raw(self, **kwargs) -> Any:
        """Not used for file adapters."""
        return {}
    
    def transform(self, raw_data: Any) -> RecrutementIndicators:
        """Transform parsed data to indicators."""
        return raw_data
    
    def parse_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse Parcoursup CSV file."""
        # Try different encodings common in French exports
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                return pd.read_csv(
                    io.BytesIO(file_content),
                    delimiter=";",
                    encoding=encoding,
                )
            except UnicodeDecodeError:
                continue
        
        # Fallback
        return pd.read_csv(io.BytesIO(file_content), delimiter=";")
    
    def parse_parcoursup_export(self, file_content: bytes, annee: int = None) -> RecrutementIndicators:
        """
        Parse Parcoursup export file.
        
        Expected columns (may vary):
        - Série du Bac / Type Bac
        - Mention au Bac
        - Département (origine)
        - Statut / Réponse
        - Rang
        """
        df = self.parse_file(file_content, "parcoursup.csv")
        df.columns = df.columns.str.lower().str.strip()
        
        annee = annee or date.today().year
        total = len(df)
        
        # Detect column names (they vary by year)
        bac_col = self._find_column(df, ["série du bac", "type bac", "bac", "série"])
        mention_col = self._find_column(df, ["mention au bac", "mention", "mention bac"])
        dept_col = self._find_column(df, ["département", "dept", "origine"])
        statut_col = self._find_column(df, ["statut", "réponse", "decision", "état"])
        lycee_col = self._find_column(df, ["lycée", "etablissement", "lycee"])
        
        # Count by status
        acceptes = 0
        confirmes = 0
        refuses = 0
        
        if statut_col:
            statuts = df[statut_col].str.lower().fillna("")
            acceptes = statuts.str.contains("accepté|oui|admis", regex=True).sum()
            confirmes = statuts.str.contains("confirmé|inscrit|définitif", regex=True).sum()
            refuses = statuts.str.contains("refusé|non|rejeté", regex=True).sum()
        
        # Count by bac type
        par_bac: dict[str, int] = {}
        if bac_col:
            par_bac = df[bac_col].value_counts().to_dict()
        
        # Count by mention
        par_mention: dict[str, int] = {}
        if mention_col:
            par_mention = df[mention_col].value_counts().to_dict()
        
        # Count by origin
        par_origine: dict[str, int] = {}
        if dept_col:
            par_origine = df[dept_col].value_counts().head(20).to_dict()
        
        # Top lycées
        top_lycees = []
        if lycee_col:
            lycee_counts = df[lycee_col].value_counts().head(10)
            top_lycees = [LyceeStats(lycee=k, count=v) for k, v in lycee_counts.items()]
        
        return RecrutementIndicators(
            annee_courante=annee,
            total_candidats=total,
            candidats_acceptes=acceptes,
            candidats_confirmes=confirmes if confirmes > 0 else acceptes,
            taux_acceptation=acceptes / total if total > 0 else 0,
            taux_confirmation=confirmes / acceptes if acceptes > 0 else 0,
            par_type_bac=par_bac,
            par_origine=par_origine,
            par_mention=par_mention,
            evolution=[],
            top_lycees=top_lycees,
        )
    
    def _find_column(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Find a column by trying multiple possible names."""
        for col in df.columns:
            col_lower = col.lower()
            for candidate in candidates:
                if candidate in col_lower:
                    return col
        return None


# Mock adapter for development
class MockParcoursupAdapter(FileAdapter[RecrutementIndicators]):
    """Mock Parcoursup adapter with sample data."""
    
    @property
    def source_name(self) -> str:
        return "Parcoursup (Mock)"
    
    async def fetch_raw(self, **kwargs) -> Any:
        return {}
    
    def transform(self, raw_data: Any) -> RecrutementIndicators:
        return self.get_mock_data()
    
    def parse_file(self, file_content: bytes, filename: str) -> Any:
        return {}
    
    def get_mock_data(self) -> RecrutementIndicators:
        """Return mock recruitment data."""
        return RecrutementIndicators(
            annee_courante=2024,
            total_candidats=850,
            candidats_acceptes=180,
            candidats_confirmes=52,
            taux_acceptation=0.21,
            taux_confirmation=0.29,
            par_type_bac={
                "Bac Général": 320,
                "Bac Techno STI2D": 280,
                "Bac Techno STMG": 120,
                "Bac Pro SN": 90,
                "Autre": 40,
            },
            par_origine={
                "59 - Nord": 180,
                "62 - Pas-de-Calais": 150,
                "80 - Somme": 85,
                "02 - Aisne": 70,
                "60 - Oise": 65,
                "Autres": 300,
            },
            par_mention={
                "Très Bien": 45,
                "Bien": 120,
                "Assez Bien": 280,
                "Passable": 350,
                "Non renseigné": 55,
            },
            evolution=[
                VoeuStats(annee=2021, nb_voeux=720, nb_acceptes=150, 
                         nb_confirmes=48, nb_refuses=570, nb_desistes=30),
                VoeuStats(annee=2022, nb_voeux=780, nb_acceptes=165,
                         nb_confirmes=50, nb_refuses=615, nb_desistes=28),
                VoeuStats(annee=2023, nb_voeux=820, nb_acceptes=175,
                         nb_confirmes=51, nb_refuses=645, nb_desistes=32),
                VoeuStats(annee=2024, nb_voeux=850, nb_acceptes=180,
                         nb_confirmes=52, nb_refuses=670, nb_desistes=35),
            ],
            top_lycees=[
                LyceeStats(lycee="Lycée Baggio - Lille", count=25),
                LyceeStats(lycee="Lycée Colbert - Tourcoing", count=18),
                LyceeStats(lycee="Lycée Branly - Boulogne", count=15),
                LyceeStats(lycee="Lycée Condorcet - Lens", count=12),
                LyceeStats(lycee="Lycée Baudelaire - Roubaix", count=10),
            ],
        )
