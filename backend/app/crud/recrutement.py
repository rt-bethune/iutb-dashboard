"""CRUD operations for Recrutement/Parcoursup (department-scoped)."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
import io
import pandas as pd
import json

from app.models.db_models import CampagneRecrutement, CandidatDB, StatistiquesParcoursup
from app.schemas.recrutement import (
    CampagneCreate,
    CampagneUpdate,
    CandidatCreate,
    CandidatUpdate,
    ParcoursupStats,
    ImportParcoursupResult,
)


# ==================== CAMPAGNE ====================

def get_campagne(db: Session, department: str, annee: int) -> Optional[CampagneRecrutement]:
    """Get campaign for a specific department and year."""
    return db.query(CampagneRecrutement).filter(
        CampagneRecrutement.department == department,
        CampagneRecrutement.annee == annee
    ).first()


def get_campagne_by_id(db: Session, campagne_id: int) -> Optional[CampagneRecrutement]:
    """Get campaign by ID."""
    return db.query(CampagneRecrutement).filter(CampagneRecrutement.id == campagne_id).first()


def get_all_campagnes(db: Session, department: str, skip: int = 0, limit: int = 100) -> list[CampagneRecrutement]:
    """Get all campaigns for a department."""
    return db.query(CampagneRecrutement).filter(
        CampagneRecrutement.department == department
    ).order_by(CampagneRecrutement.annee.desc()).offset(skip).limit(limit).all()


def create_campagne(db: Session, department: str, campagne: CampagneCreate) -> CampagneRecrutement:
    """Create a new recruitment campaign for a department."""
    db_campagne = CampagneRecrutement(
        department=department,
        annee=campagne.annee,
        nb_places=campagne.nb_places,
        date_debut=campagne.date_debut,
        date_fin=campagne.date_fin,
        rang_dernier_appele=campagne.rang_dernier_appele,
    )
    db.add(db_campagne)
    db.commit()
    db.refresh(db_campagne)
    return db_campagne


def update_campagne(db: Session, department: str, annee: int, campagne: CampagneUpdate) -> Optional[CampagneRecrutement]:
    """Update a campaign."""
    db_campagne = get_campagne(db, department, annee)
    if not db_campagne:
        return None
    
    update_data = campagne.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_campagne, field, value)
    
    db_campagne.date_modification = date.today()
    db.commit()
    db.refresh(db_campagne)
    return db_campagne


def delete_campagne(db: Session, department: str, annee: int) -> bool:
    """Delete a campaign and all its candidates."""
    db_campagne = get_campagne(db, department, annee)
    if not db_campagne:
        return False
    
    db.delete(db_campagne)
    db.commit()
    return True


def get_or_create_campagne(db: Session, department: str, annee: int) -> CampagneRecrutement:
    """Get existing campaign or create a new one."""
    campagne = get_campagne(db, department, annee)
    if not campagne:
        campagne = create_campagne(db, department, CampagneCreate(annee=annee))
    return campagne


# ==================== CANDIDAT ====================

def get_candidats(
    db: Session,
    campagne_id: int,
    statut: Optional[str] = None,
    type_bac: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[CandidatDB]:
    """Get candidates with optional filters."""
    query = db.query(CandidatDB).filter(CandidatDB.campagne_id == campagne_id)
    
    if statut:
        query = query.filter(CandidatDB.statut == statut)
    if type_bac:
        query = query.filter(CandidatDB.type_bac == type_bac)
    
    return query.order_by(CandidatDB.rang_appel).offset(skip).limit(limit).all()


def get_candidat(db: Session, candidat_id: int) -> Optional[CandidatDB]:
    """Get a specific candidate."""
    return db.query(CandidatDB).filter(CandidatDB.id == candidat_id).first()


def get_candidat_by_numero(db: Session, campagne_id: int, numero: str) -> Optional[CandidatDB]:
    """Get candidate by Parcoursup number."""
    return db.query(CandidatDB).filter(
        CandidatDB.campagne_id == campagne_id,
        CandidatDB.numero_candidat == numero
    ).first()


def create_candidat(db: Session, campagne_id: int, candidat: CandidatCreate) -> CandidatDB:
    """Create a new candidate."""
    db_candidat = CandidatDB(
        campagne_id=campagne_id,
        numero_candidat=candidat.numero_candidat,
        nom=candidat.nom,
        prenom=candidat.prenom,
        type_bac=candidat.type_bac,
        serie_bac=candidat.serie_bac,
        mention_bac=candidat.mention_bac,
        annee_bac=candidat.annee_bac,
        departement_origine=candidat.departement_origine,
        pays_origine=candidat.pays_origine,
        lycee=candidat.lycee,
        code_lycee=candidat.code_lycee,
        rang_voeu=candidat.rang_voeu,
        rang_appel=candidat.rang_appel,
        statut=candidat.statut,
        date_reponse=candidat.date_reponse,
    )
    db.add(db_candidat)
    db.commit()
    db.refresh(db_candidat)
    return db_candidat


def create_candidats_bulk(db: Session, campagne_id: int, candidats: list[CandidatCreate]) -> list[CandidatDB]:
    """Create multiple candidates."""
    db_candidats = []
    for candidat in candidats:
        db_candidat = CandidatDB(
            campagne_id=campagne_id,
            numero_candidat=candidat.numero_candidat,
            nom=candidat.nom,
            prenom=candidat.prenom,
            type_bac=candidat.type_bac,
            serie_bac=candidat.serie_bac,
            mention_bac=candidat.mention_bac,
            annee_bac=candidat.annee_bac,
            departement_origine=candidat.departement_origine,
            pays_origine=candidat.pays_origine,
            lycee=candidat.lycee,
            code_lycee=candidat.code_lycee,
            rang_voeu=candidat.rang_voeu,
            rang_appel=candidat.rang_appel,
            statut=candidat.statut,
            date_reponse=candidat.date_reponse,
        )
        db_candidats.append(db_candidat)
    
    db.add_all(db_candidats)
    db.commit()
    return db_candidats


def update_candidat(db: Session, candidat_id: int, candidat: CandidatUpdate) -> Optional[CandidatDB]:
    """Update a candidate."""
    db_candidat = get_candidat(db, candidat_id)
    if not db_candidat:
        return None
    
    update_data = candidat.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_candidat, field, value)
    
    db.commit()
    db.refresh(db_candidat)
    return db_candidat


def delete_candidat(db: Session, candidat_id: int) -> bool:
    """Delete a candidate."""
    db_candidat = get_candidat(db, candidat_id)
    if not db_candidat:
        return False
    
    db.delete(db_candidat)
    db.commit()
    return True


# ==================== IMPORT PARCOURSUP ====================

def import_parcoursup_from_csv(db: Session, department: str, file_content: bytes, annee: int) -> ImportParcoursupResult:
    """Import Parcoursup data from CSV file for a department."""
    try:
        # Try different encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(io.BytesIO(file_content), sep=";", encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Impossible de décoder le fichier CSV")
        
        df.columns = df.columns.str.lower().str.strip()
        
        # Get or create campaign for department
        campagne = get_or_create_campagne(db, department, annee)
        
        candidats_importes = 0
        candidats_mis_a_jour = 0
        erreurs = []
        
        # Column mappings (Parcoursup export format)
        col_map = {
            "numero": ["n° candidat", "numero_candidat", "n°candidat", "numero"],
            "nom": ["nom", "nom candidat"],
            "prenom": ["prénom", "prenom", "prénom candidat"],
            "type_bac": ["type bac", "type_bac", "série bac", "bac"],
            "mention": ["mention bac", "mention", "mention_bac"],
            "departement": ["département", "departement", "dept origine", "dept"],
            "lycee": ["lycée", "lycee", "établissement origine", "lycée origine"],
            "rang": ["rang", "rang appel", "rang_appel"],
            "statut": ["statut", "réponse", "reponse", "état"],
        }
        
        def get_col(row, names):
            for name in names:
                if name in row.index and pd.notna(row[name]):
                    return str(row[name]).strip()
            return None
        
        # Statut mapping
        statut_map = {
            "oui": "accepte",
            "oui définitif": "confirme",
            "non": "refuse",
            "en attente": "en_attente",
            "démission": "desiste",
            "accepté": "accepte",
            "confirmé": "confirme",
            "refusé": "refuse",
            "désisté": "desiste",
        }
        
        for idx, row in df.iterrows():
            try:
                numero = get_col(row, col_map["numero"])
                
                # Parse statut
                statut_raw = get_col(row, col_map["statut"]) or "en_attente"
                statut = statut_map.get(statut_raw.lower(), "en_attente")
                
                # Parse type bac
                type_bac = get_col(row, col_map["type_bac"]) or "Inconnu"
                if "général" in type_bac.lower() or "gen" in type_bac.lower():
                    type_bac = "Général"
                elif "techno" in type_bac.lower() or "sti" in type_bac.lower():
                    type_bac = "Technologique"
                elif "pro" in type_bac.lower():
                    type_bac = "Professionnel"
                
                # Parse rang
                rang_str = get_col(row, col_map["rang"])
                rang = int(rang_str) if rang_str and rang_str.isdigit() else None
                
                # Check if candidate exists
                existing = None
                if numero:
                    existing = get_candidat_by_numero(db, campagne.id, numero)
                
                if existing:
                    # Update existing
                    existing.statut = statut
                    existing.type_bac = type_bac
                    existing.mention_bac = get_col(row, col_map["mention"])
                    existing.departement_origine = get_col(row, col_map["departement"])
                    existing.lycee = get_col(row, col_map["lycee"])
                    existing.rang_appel = rang
                    candidats_mis_a_jour += 1
                else:
                    # Create new
                    db_candidat = CandidatDB(
                        campagne_id=campagne.id,
                        numero_candidat=numero,
                        nom=get_col(row, col_map["nom"]),
                        prenom=get_col(row, col_map["prenom"]),
                        type_bac=type_bac,
                        mention_bac=get_col(row, col_map["mention"]),
                        departement_origine=get_col(row, col_map["departement"]),
                        lycee=get_col(row, col_map["lycee"]),
                        rang_appel=rang,
                        statut=statut,
                    )
                    db.add(db_candidat)
                    candidats_importes += 1
                
            except Exception as e:
                erreurs.append(f"Ligne {idx + 2}: {str(e)}")
        
        db.commit()
        
        # Update statistics
        _update_stats(db, department, campagne.id, annee)
        
        return ImportParcoursupResult(
            success=True,
            message=f"Import réussi pour l'année {annee}",
            annee=annee,
            candidats_importes=candidats_importes,
            candidats_mis_a_jour=candidats_mis_a_jour,
            erreurs=erreurs,
        )
        
    except Exception as e:
        db.rollback()
        return ImportParcoursupResult(
            success=False,
            message=f"Erreur lors de l'import: {str(e)}",
            annee=annee,
            erreurs=[str(e)],
        )


def import_parcoursup_from_excel(db: Session, department: str, file_content: bytes, annee: int) -> ImportParcoursupResult:
    """Import Parcoursup data from Excel file for a department."""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        # Convert to CSV bytes and use existing parser
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8")
        csv_buffer.seek(0)
        return import_parcoursup_from_csv(db, department, csv_buffer.read(), annee)
    except Exception as e:
        return ImportParcoursupResult(
            success=False,
            message=f"Erreur lors de la lecture du fichier Excel: {str(e)}",
            annee=annee,
            erreurs=[str(e)],
        )


# ==================== STATISTICS ====================

def save_direct_stats(
    db: Session, 
    department: str,
    annee: int, 
    nb_voeux: int,
    nb_acceptes: int,
    nb_confirmes: int,
    nb_refuses: int = 0,
    nb_desistes: int = 0,
    par_type_bac: dict = None,
    par_mention: dict = None,
    par_origine: dict = None,
    par_lycees: dict = None,
) -> StatistiquesParcoursup:
    """
    Save statistics directly without creating individual candidates.
    This is useful for quick entry of aggregate data.
    """
    # Create or get campaign
    campagne = get_campagne(db, department, annee)
    if not campagne:
        campagne = create_campagne(db, department, CampagneCreate(annee=annee))
    
    # Update or create stats
    stats = db.query(StatistiquesParcoursup).filter(
        StatistiquesParcoursup.department == department,
        StatistiquesParcoursup.annee == annee
    ).first()
    if not stats:
        stats = StatistiquesParcoursup(department=department, annee=annee)
        db.add(stats)
    
    stats.nb_voeux = nb_voeux
    stats.nb_acceptes = nb_acceptes
    stats.nb_confirmes = nb_confirmes
    stats.nb_refuses = nb_refuses
    stats.nb_desistes = nb_desistes
    stats.par_type_bac = json.dumps(par_type_bac or {})
    stats.par_mention = json.dumps(par_mention or {})
    stats.par_origine = json.dumps(par_origine or {})
    stats.par_lycees = json.dumps(par_lycees or {})
    stats.date_mise_a_jour = date.today()
    
    db.commit()
    db.refresh(stats)
    return stats


def _update_stats(db: Session, department: str, campagne_id: int, annee: int):
    """Update aggregated statistics for a campaign."""
    candidats = db.query(CandidatDB).filter(CandidatDB.campagne_id == campagne_id).all()
    
    # Count by status
    nb_voeux = len(candidats)
    nb_acceptes = sum(1 for c in candidats if c.statut in ["accepte", "confirme"])
    nb_confirmes = sum(1 for c in candidats if c.statut == "confirme")
    nb_refuses = sum(1 for c in candidats if c.statut == "refuse")
    nb_desistes = sum(1 for c in candidats if c.statut == "desiste")
    
    # Group by type bac
    par_type_bac = {}
    for c in candidats:
        par_type_bac[c.type_bac] = par_type_bac.get(c.type_bac, 0) + 1
    
    # Group by mention
    par_mention = {}
    for c in candidats:
        mention = c.mention_bac or "Non renseignée"
        par_mention[mention] = par_mention.get(mention, 0) + 1
    
    # Group by origin
    par_origine = {}
    for c in candidats:
        origine = c.departement_origine or c.pays_origine or "Inconnue"
        par_origine[origine] = par_origine.get(origine, 0) + 1
    
    # Update or create stats
    stats = db.query(StatistiquesParcoursup).filter(
        StatistiquesParcoursup.department == department,
        StatistiquesParcoursup.annee == annee
    ).first()
    if not stats:
        stats = StatistiquesParcoursup(department=department, annee=annee)
        db.add(stats)
    
    stats.nb_voeux = nb_voeux
    stats.nb_acceptes = nb_acceptes
    stats.nb_confirmes = nb_confirmes
    stats.nb_refuses = nb_refuses
    stats.nb_desistes = nb_desistes
    stats.par_type_bac = json.dumps(par_type_bac)
    stats.par_mention = json.dumps(par_mention)
    stats.par_origine = json.dumps(par_origine)
    stats.date_mise_a_jour = date.today()
    
    db.commit()


def get_parcoursup_stats(db: Session, department: str, annee: int) -> Optional[ParcoursupStats]:
    """Get Parcoursup statistics for a department and year."""
    campagne = get_campagne(db, department, annee)
    if not campagne:
        return None
    
    # Check if we have candidats - if so, update stats from them
    candidat_count = db.query(CandidatDB).filter(CandidatDB.campagne_id == campagne.id).count()
    if candidat_count > 0:
        _update_stats(db, department, campagne.id, annee)
    
    stats = db.query(StatistiquesParcoursup).filter(
        StatistiquesParcoursup.department == department,
        StatistiquesParcoursup.annee == annee
    ).first()
    if not stats:
        return None
    
    # Parse JSON fields
    par_type_bac = json.loads(stats.par_type_bac) if stats.par_type_bac else {}
    par_mention = json.loads(stats.par_mention) if stats.par_mention else {}
    par_origine = json.loads(stats.par_origine) if stats.par_origine else {}
    par_lycees = json.loads(stats.par_lycees) if stats.par_lycees else {}
    
    # Get top lycees - from par_lycees if available, otherwise from candidats
    if par_lycees:
        # Use manually entered lycées data
        top_lycees = [{"lycee": k, "count": v} for k, v in sorted(par_lycees.items(), key=lambda x: x[1], reverse=True)[:10]]
    else:
        # Fallback: compute from candidats
        top_lycees_query = db.query(
            CandidatDB.lycee,
            func.count(CandidatDB.id).label("count")
        ).filter(
            CandidatDB.campagne_id == campagne.id,
            CandidatDB.lycee.isnot(None)
        ).group_by(CandidatDB.lycee).order_by(func.count(CandidatDB.id).desc()).limit(10).all()
        
        top_lycees = [{"lycee": l.lycee, "count": l.count} for l in top_lycees_query]
    
    return ParcoursupStats(
        annee=annee,
        nb_voeux=stats.nb_voeux,
        nb_acceptes=stats.nb_acceptes,
        nb_confirmes=stats.nb_confirmes,
        nb_refuses=stats.nb_refuses,
        nb_desistes=stats.nb_desistes,
        taux_acceptation=stats.nb_acceptes / stats.nb_voeux if stats.nb_voeux > 0 else 0,
        taux_confirmation=stats.nb_confirmes / stats.nb_acceptes if stats.nb_acceptes > 0 else 0,
        par_type_bac=par_type_bac,
        par_mention=par_mention,
        par_origine=par_origine,
        top_lycees=top_lycees,
    )


def get_evolution_recrutement(db: Session, department: str, limit: int = 5) -> dict:
    """Get recruitment evolution over years for a department."""
    campagnes = db.query(CampagneRecrutement).filter(
        CampagneRecrutement.department == department
    ).order_by(CampagneRecrutement.annee.desc()).limit(limit).all()
    
    annees = []
    nb_voeux = []
    nb_confirmes = []
    taux_remplissage = []
    
    for campagne in reversed(campagnes):
        stats = db.query(StatistiquesParcoursup).filter(
            StatistiquesParcoursup.department == department,
            StatistiquesParcoursup.annee == campagne.annee
        ).first()
        if stats:
            annees.append(campagne.annee)
            nb_voeux.append(stats.nb_voeux)
            nb_confirmes.append(stats.nb_confirmes)
            taux = stats.nb_confirmes / campagne.nb_places if campagne.nb_places > 0 else 0
            taux_remplissage.append(round(taux, 2))
    
    return {
        "annees": annees,
        "nb_voeux": nb_voeux,
        "nb_confirmes": nb_confirmes,
        "taux_remplissage": taux_remplissage,
    }
