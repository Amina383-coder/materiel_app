import sys
import csv
import unicodedata
from pathlib import Path
from database.database import db


def strip_accents(text: str) -> str:
    if not text:
        return ''
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )


def sanitize_token(text: str) -> str:
    t = strip_accents(text or '')
    t = t.replace("'", ' ').replace('"', ' ').replace(',', ' ').replace(';', ' ')
    t = ''.join(ch if ch.isalnum() or ch in ['.', '-', '_'] else '-' for ch in t)
    return '-'.join(filter(None, t.split('-'))).lower()


def build_username(prenom: str, nom: str) -> str:
    first = sanitize_token(prenom)
    last = sanitize_token(nom)
    return f"{first}.{last}" if first and last else (first or last)


def build_email(username: str, domain: str = 'sedima.local') -> str:
    base = username or 'user'
    return f"{base}@{domain}"


def normalize_key(text: str) -> str:
    t = strip_accents((text or '').strip()).lower()
    for ch in [' ', '.', '&', "'", '"']:
        t = t.replace(ch, '')
    return t


SERVICE_CANONICAL_MAP = {
    # key (normalized) -> canonical name as in DB seed
    'it': 'Informatique',
    'qhse': 'QHSE',
    'q.h.s.e': 'QHSE',
    'finance&comptabilite': 'Finance et comptabilité',
    'marketing&commercial': 'Commercial',
    'supplychain': 'Supply chain',
}


def canonicalize_service(raw_service: str) -> str:
    if not raw_service:
        return ''
    key = normalize_key(raw_service)
    return SERVICE_CANONICAL_MAP.get(key, raw_service.strip())


def find_or_create_service(service_name: str) -> int | None:
    name = canonicalize_service(service_name)
    if not name:
        return None
    # Try to find
    rows = db.execute_query("SELECT id FROM services WHERE nom = %s", (name,))
    if rows:
        return rows[0]['id']
    # Create if missing
    rc = db.execute_query("INSERT INTO services (nom) VALUES (%s)", (name,))
    if rc is None:
        return None
    return db.get_last_insert_id()


def ensure_unique_username(base_username: str) -> str:
    if not base_username:
        base_username = 'user'
    candidate = base_username
    suffix = 1
    while True:
        rows = db.execute_query("SELECT id FROM utilisateurs WHERE nom_utilisateur = %s", (candidate,))
        if not rows:
            return candidate
        suffix += 1
        candidate = f"{base_username}-{suffix}"


def find_or_create_employe(nom_affichage: str, service_id: int | None) -> int | None:
    if not nom_affichage:
        return None
    rows = db.execute_query(
        "SELECT id FROM employes WHERE nom = %s AND (service_id = %s OR (%s IS NULL AND service_id IS NULL))",
        (nom_affichage, service_id, service_id)
    )
    if rows:
        return rows[0]['id']
    rc = db.execute_query("INSERT INTO employes (nom, service_id) VALUES (%s, %s)", (nom_affichage, service_id))
    if rc is None:
        return None
    return db.get_last_insert_id()


def import_users(csv_path: Path, default_password: str = '123456') -> int:
    if not csv_path.exists():
        print(f"Fichier introuvable: {csv_path}")
        return 0

    if not db.connect():
        print("Connexion DB échouée")
        return 0

    inserted = 0
    with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        for idx, row in enumerate(reader, start=1):
            if not row or len(row) < 3:
                continue
            service_raw, nom, prenom = (row[0] or '').strip(), (row[1] or '').strip(), (row[2] or '').strip()
            # Skip header
            if normalize_key(service_raw) in ('departement',) and normalize_key(nom) in ('nom',) and normalize_key(prenom) in ('prenom',):
                continue
            if not nom and not prenom:
                continue

            username = build_username(prenom, nom)
            username = ensure_unique_username(username)
            email = build_email(username)

            # Résoudre le service canonique et récupérer son id
            service_name = canonicalize_service(service_raw)
            service_id = find_or_create_service(service_name) if service_name else None

            # Insérer l'utilisateur (mot de passe en clair pour correspondre au login actuel)
            q = (
                "INSERT INTO utilisateurs (nom_utilisateur, email, mot_de_passe_hash, role, actif) "
                "VALUES (%s, %s, %s, 'user', TRUE) "
                "ON DUPLICATE KEY UPDATE email=VALUES(email), actif=VALUES(actif)"
            )
            rc = db.execute_query(q, (username, email, default_password))
            if rc is not None:
                inserted += 1

            # Créer un employé lié au service (affichage: Prenom Nom)
            nom_affichage = ' '.join(part for part in [prenom.strip(), nom.strip()] if part)
            try:
                find_or_create_employe(nom_affichage, service_id)
            except Exception:
                pass

    db.disconnect()
    return inserted


def main():
    if len(sys.argv) < 2:
        print("Usage: python backend/import_users.py <CHEMIN_CSV> [motdepasse_par_defaut]")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    default_password = sys.argv[2] if len(sys.argv) > 2 else '123456'
    count = import_users(csv_path, default_password)
    print(f"Utilisateurs traités: {count}")


if __name__ == '__main__':
    main()


