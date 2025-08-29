from flask import Blueprint, request, jsonify, render_template, send_from_directory, current_app, url_for, redirect, session
from database.database import db
import json
import logging
from datetime import datetime

# Blueprint pour les pages principales
main_bp = Blueprint('main', __name__)

# Blueprint pour l'API
api_bp = Blueprint('api', __name__)

# Utilitaires
def _nz(value):
    """Retourne None si value est vide ('', None), sinon la valeur d'origine."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == '':
        return None
    return value

def generate_numero_fiche(type_operation):
    """Génère un numéro de fiche unique au format: type-date-001"""
    try:
        # Mapping des types d'opération vers les préfixes
        prefix_map = {
            'attribution': 'ATB',
            'restitution': 'RST',
            'incident': 'ICD'
        }
        prefix = prefix_map.get(type_operation, 'OPR')
        
        # Date actuelle au format YYYYMMDD
        today = datetime.now().strftime('%Y%m%d')
        
        # Chercher le dernier numéro pour aujourd'hui et ce type
        query = """
            SELECT numero_fiche FROM operations 
            WHERE numero_fiche LIKE %s 
            ORDER BY numero_fiche DESC 
            LIMIT 1
        """
        pattern = f"{prefix}-{today}-%"
        last_num = db.execute_query(query, (pattern,))
        
        if last_num and len(last_num) > 0:
            # Extraire le numéro et incrémenter
            last_num_str = last_num[0]['numero_fiche']
            parts = last_num_str.split('-')
            if len(parts) == 3:
                try:
                    current_num = int(parts[2])
                    new_num = current_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
        else:
            new_num = 1
        
        # Formater avec des zéros (001, 002, etc.)
        return f"{prefix}-{today}-{new_num:03d}"
        
    except Exception as e:
        logging.error(f"Erreur lors de la génération du numéro de fiche: {e}")
        # Fallback: timestamp
        timestamp = int(datetime.now().timestamp())
        return f"{prefix}-{today}-{timestamp}"

@main_bp.route('/')
def index():
    """Page d'accueil - rend le template d'attribution"""
    return render_template('index.html')

@main_bp.route('/attribution')
def attribution():
    """Page d'attribution"""
    return render_template('index.html')

@main_bp.route('/restitution')
def restitution():
    """Page de restitution"""
    return render_template('restitution.html')

@main_bp.route('/historique')
def historique():
    """Page d'historique"""
    return render_template('historique.html')

@main_bp.route('/incident')
def incident():
    """Page de signalisation d'incident"""
    return render_template('incident.html')

# Supprimer les routes custom qui interceptaient le static. Flask sert /static/ automatiquement.

# Sécurité: exiger l'authentification pour les pages
@main_bp.before_request
def require_login():
    # Autoriser l'accès à la page de connexion
    if request.endpoint in ('main.login', 'static'):
        return
    # Autoriser les favicons éventuels
    if request.path.startswith('/favicon'):
        return
    # Exiger une session utilisateur pour toutes les autres pages du blueprint
    if not session.get('user_id') and request.endpoint and request.endpoint.startswith('main.'):
        return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    try:
        payload = request.get_json(silent=True) or request.form
        username = (payload.get('username') or '').strip()
        password = (payload.get('password') or '').strip()
        if not username or not password:
            return jsonify({'success': False, 'error': 'Identifiants requis'}), 400

        user_rows = db.execute_query(
            "SELECT id, nom_utilisateur, mot_de_passe_hash, actif FROM utilisateurs WHERE nom_utilisateur = %s",
            (username,)
        )
        if not user_rows:
            return jsonify({'success': False, 'error': 'Utilisateur introuvable'}), 401
        user = user_rows[0]
        if not user.get('actif'):
            return jsonify({'success': False, 'error': 'Compte désactivé'}), 403

        # Comparaison simple (le champ peut contenir un mot de passe en clair ou hash selon votre configuration)
        if password != (user.get('mot_de_passe_hash') or ''):
            return jsonify({'success': False, 'error': 'Mot de passe incorrect'}), 401

        session['user_id'] = user['id']
        session['username'] = user['nom_utilisateur']
        return jsonify({'success': True, 'redirect': url_for('main.attribution')})
    except Exception as e:
        logging.error(f"Erreur de connexion: {e}")
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

# Routes API
@api_bp.route('/services', methods=['GET'])
def get_services():
    """Récupérer tous les services"""
    try:
        query = "SELECT * FROM services ORDER BY nom"
        services = db.execute_query(query)
        return jsonify({'success': True, 'data': services})
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des services: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/types-materiel', methods=['GET'])
def get_types_materiel():
    """Récupérer tous les types de matériel"""
    try:
        query = "SELECT * FROM types_materiel ORDER BY nom"
        types = db.execute_query(query)
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/attribution', methods=['POST'])
def create_attribution():
    """Créer une nouvelle attribution"""
    try:
        data = request.get_json()
        
        # Vérifier les données requises
        required_fields = ['nom', 'service', 'materiels', 'redaction', 'validation', 'destinataire', 'signatures']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Champ manquant: {field}'}), 400
        
        # Récupérer le service
        service_rows = db.execute_query("SELECT id FROM services WHERE nom = %s", (data['service'],))
        if not service_rows:
            return jsonify({'success': False, 'error': "Service introuvable"}), 404
        service_id = service_rows[0]['id']

        # Récupérer ou créer l'employé (nom + service)
        employe_rows = db.execute_query(
            "SELECT id FROM employes WHERE nom = %s AND service_id = %s",
            (data['nom'], service_id)
        )
        if employe_rows:
            employe_id = employe_rows[0]['id']
        else:
            insert_emp_rc = db.execute_query(
                "INSERT INTO employes (nom, service_id) VALUES (%s, %s)",
                (data['nom'], service_id)
            )
            if insert_emp_rc is None:
                raise Exception("Échec d'insertion de l'employé")
            employe_id = db.get_last_insert_id()
            if not employe_id:
                raise Exception("Impossible de récupérer l'identifiant de l'employé")
        
        # Traiter chaque matériel
        operations = []
        
        # Générer le numéro de fiche automatiquement (une seule fois pour toutes les opérations)
        numero_fiche = generate_numero_fiche('attribution')
        
        for materiel_data in data['materiels']:
            # Upsert matériel et récupérer son id de façon fiable même en cas de doublon
            materiel_query = """
                INSERT INTO materiels (type_id, modele, numero_serie, service_achat, date_achat, statut)
                VALUES (
                    (SELECT id FROM types_materiel WHERE nom = %s),
                    %s, %s, %s, %s, 'attribue'
                )
                ON DUPLICATE KEY UPDATE
                    id = LAST_INSERT_ID(id),
                    statut = 'attribue',
                    modele = VALUES(modele),
                    service_achat = VALUES(service_achat),
                    date_achat = VALUES(date_achat),
                    type_id = VALUES(type_id)
            """
            upsert_rc = db.execute_query(materiel_query, (
                materiel_data['type'],
                materiel_data['modele'],
                materiel_data['serie'],
                materiel_data.get('serviceAchat', ''),
                _nz(materiel_data.get('dateRemise'))
            ))
            if upsert_rc is None:
                raise Exception("Échec d'insertion/mise à jour du matériel")
            materiel_id = db.get_last_insert_id()
            if not materiel_id:
                raise Exception("Impossible de récupérer l'identifiant du matériel")
            
            # Créer l'opération d'attribution
            operation_query = """
                INSERT INTO operations (numero_fiche, type_operation, employe_id, materiel_id, date_operation, date_remise, motif)
                VALUES (%s, 'attribution', %s, %s, %s, %s, %s)
            """
            op_rc = db.execute_query(operation_query, (
                numero_fiche,
                employe_id,
                materiel_id,
                datetime.now().date(),
                _nz(materiel_data.get('dateRemise')),
                _nz(data.get('motif'))
            ))
            if op_rc is None:
                raise Exception("Échec de création de l'opération d'attribution")
            operation_id = db.get_last_insert_id()
            if not operation_id:
                raise Exception("Impossible de récupérer l'identifiant de l'opération")
            operations.append(operation_id)
        
        # Insérer les signatures
        if not operations:
            raise Exception("Aucune opération créée")
        signatures_data = [
            (operations[0], 'redaction', data['redaction']['nom'], data['redaction']['fonction'], 
             data['redaction']['date'], data['signatures']['redaction']),
            (operations[0], 'validation', data['validation']['nom'], data['validation']['fonction'], 
             data['validation']['date'], data['signatures']['validation']),
            (operations[0], 'destinataire', data['destinataire']['nom'], data['destinataire']['fonction'], 
             data['destinataire']['date'], data['signatures']['destinataire'])
        ]
        
        signature_query = """
            INSERT INTO signatures (operation_id, type_signature, nom, fonction, date_signature, fichier_signature)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        sig_rc = db.execute_many(signature_query, signatures_data)
        if sig_rc is None:
            raise Exception("Échec d'enregistrement des signatures")
        
        return jsonify({
            'success': True, 
            'message': 'Attribution créée avec succès',
            'operation_ids': operations,
            'numero_fiche': numero_fiche
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la création de l'attribution: {e}")
        if current_app.config.get('DEBUG'):
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': "Une erreur interne est survenue. Merci de contacter l'administrateur."}), 500

@api_bp.route('/restitution', methods=['POST'])
def create_restitution():
    """Créer une nouvelle restitution"""
    try:
        data = request.get_json()
        logging.info(f"Données reçues pour restitution: {data}")
        
        # Vérifier les données requises
        required_fields = ['nom', 'service', 'materiels', 'redaction', 'validation', 'destinataire', 'signatures']
        for field in required_fields:
            if field not in data:
                logging.error(f"Champ manquant: {field}")
                return jsonify({'success': False, 'error': f'Champ manquant: {field}'}), 400
        
        # Récupérer le service
        service_rows = db.execute_query("SELECT id FROM services WHERE nom = %s", (data['service'],))
        if not service_rows:
            return jsonify({'success': False, 'error': "Service introuvable"}), 404
        service_id = service_rows[0]['id']

        # Récupérer ou créer l'employé (nom + service)
        employe_rows = db.execute_query(
            "SELECT id FROM employes WHERE nom = %s AND service_id = %s",
            (data['nom'], service_id)
        )
        if employe_rows:
            employe_id = employe_rows[0]['id']
        else:
            insert_emp_rc = db.execute_query(
                "INSERT INTO employes (nom, service_id) VALUES (%s, %s)",
                (data['nom'], service_id)
            )
            if insert_emp_rc is None:
                raise Exception("Échec d'insertion de l'employé")
            employe_id = db.get_last_insert_id()
            if not employe_id:
                raise Exception("Impossible de récupérer l'identifiant de l'employé")
        
        # Traiter chaque matériel
        operations = []
        
        # Générer le numéro de fiche automatiquement (une seule fois pour toutes les opérations)
        numero_fiche = generate_numero_fiche('restitution')
        
        for materiel_data in data['materiels']:
            # Upsert matériel et récupérer son id de façon fiable même en cas de doublon
            materiel_query = """
                INSERT INTO materiels (type_id, modele, numero_serie, service_achat, date_achat, statut)
                VALUES (
                    (SELECT id FROM types_materiel WHERE nom = %s),
                    %s, %s, %s, %s, 'disponible'
                )
                ON DUPLICATE KEY UPDATE
                    id = LAST_INSERT_ID(id),
                    statut = 'disponible',
                    modele = VALUES(modele),
                    service_achat = VALUES(service_achat),
                    date_achat = VALUES(date_achat),
                    type_id = VALUES(type_id)
            """
            upsert_rc = db.execute_query(materiel_query, (
                materiel_data['type'],
                materiel_data['modele'],
                materiel_data['serie'],
                'Service non spécifié',  # Valeur par défaut
                None  # Date d'achat non spécifiée
            ))
            if upsert_rc is None:
                raise Exception("Échec d'insertion/mise à jour du matériel")
            materiel_id = db.get_last_insert_id()
            if not materiel_id:
                raise Exception("Impossible de récupérer l'identifiant du matériel")
            
            # Créer l'opération de restitution
            operation_query = """
                INSERT INTO operations (numero_fiche, type_operation, employe_id, materiel_id, date_operation, date_restitution, motif)
                VALUES (%s, 'restitution', %s, %s, %s, %s, %s)
            """
            op_rc = db.execute_query(operation_query, (
                numero_fiche,
                employe_id,
                materiel_id,
                datetime.now().date(),
                _nz(materiel_data.get('dateRestitution')),
                _nz(data.get('motif'))
            ))
            if op_rc is None:
                raise Exception("Échec de création de l'opération de restitution")
            operation_id = db.get_last_insert_id()
            if not operation_id:
                raise Exception("Impossible de récupérer l'identifiant de l'opération")
            operations.append(operation_id)
            
            # Mettre à jour le statut du matériel
            update_materiel_query = "UPDATE materiels SET statut = 'disponible' WHERE id = %s"
            upd_rc = db.execute_query(update_materiel_query, (materiel_id,))
            if upd_rc is None:
                raise Exception("Échec de mise à jour du statut du matériel")
        
        # Insérer les signatures
        if not operations:
            raise Exception("Aucune opération créée")
        signatures_data = [
            (operations[0], 'redaction', data['redaction']['nom'], data['redaction']['fonction'], 
             data['redaction']['date'], data['signatures']['redaction']),
            (operations[0], 'validation', data['validation']['nom'], data['validation']['fonction'], 
             data['validation']['date'], data['signatures']['validation']),
            (operations[0], 'destinataire', data['destinataire']['nom'], data['destinataire']['fonction'], 
             data['destinataire']['date'], data['signatures']['destinataire'])
        ]
        
        signature_query = """
            INSERT INTO signatures (operation_id, type_signature, nom, fonction, date_signature, fichier_signature)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        sig_rc = db.execute_many(signature_query, signatures_data)
        if sig_rc is None:
            raise Exception("Échec d'enregistrement des signatures")
        
        return jsonify({
            'success': True, 
            'message': 'Restitution créée avec succès',
            'operation_ids': operations,
            'numero_fiche': numero_fiche
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la création de la restitution: {e}")
        if current_app.config.get('DEBUG'):
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': "Une erreur interne est survenue. Merci de contacter l'administrateur."}), 500

@api_bp.route('/historique', methods=['GET'])
def get_historique():
    """Récupérer l'historique des opérations et incidents avec filtres"""
    try:
        # Paramètres de filtrage
        employe = request.args.get('employe', '')
        service = request.args.get('service', '')
        type_materiel = request.args.get('type_materiel', '')
        serie = request.args.get('serie', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')
        type_operation_filter = request.args.get('type_operation', '')
        
        # Construction de la requête unifiée pour toutes les opérations
        query = """
            SELECT 
                o.id,
                o.numero_fiche,
                o.type_operation,
                o.date_operation,
                o.date_remise,
                o.date_restitution,
                o.motif,
                -- Champs pour les opérations (attributions/restitutions)
                e.nom as employe_nom,
                s.nom as service_nom,
                m.modele,
                m.numero_serie,
                tm.nom as type_materiel,
                -- Champs pour les incidents
                o.declarant_nom,
                o.telephone,
                o.email,
                o.poste,
                o.numero_serie_actif,
                o.actifs_json,
                o.natures_json,
                o.autres_infos,
                o.signature_png,
                -- Type de source pour différencier
                CASE 
                    WHEN o.type_operation = 'incident' THEN 'incident'
                    ELSE 'operation'
                END as source_type
            FROM operations o
            LEFT JOIN employes e ON o.employe_id = e.id
            LEFT JOIN services s ON e.service_id = s.id
            LEFT JOIN materiels m ON o.materiel_id = m.id
            LEFT JOIN types_materiel tm ON m.type_id = tm.id
            WHERE 1=1
        """
        
        params = []
        
        # Filtres communs
        if date_debut:
            query += " AND o.date_operation >= %s"
            params.append(date_debut)
        
        if date_fin:
            query += " AND o.date_operation <= %s"
            params.append(date_fin)
        
        # Filtres spécifiques
        if employe and (not service or not type_materiel or not serie):
            query += " AND (e.nom LIKE %s OR o.declarant_nom LIKE %s)"
            params.extend([f'%{employe}%', f'%{employe}%'])
        elif employe:
            query += " AND (e.nom LIKE %s OR o.declarant_nom LIKE %s)"
            params.extend([f'%{employe}%', f'%{employe}%'])
        
        if service:
            query += " AND s.nom = %s"
            params.append(service)
        
        if type_materiel:
            query += " AND tm.nom LIKE %s"
            params.append(f'%{type_materiel}%')
        
        if serie:
            query += " AND (m.numero_serie LIKE %s OR o.numero_serie_actif LIKE %s)"
            params.extend([f'%{serie}%', f'%{serie}%'])

        if type_operation_filter:
            query += " AND o.type_operation = %s"
            params.append(type_operation_filter)
        
        query += " ORDER BY o.date_operation DESC, o.id DESC"
        
        operations = db.execute_query(query, params)
        
        # Traiter les données pour uniformiser l'affichage
        for op in operations:
            if op['type_operation'] == 'incident':
                # Utiliser les champs spécifiques et tenter de remplir service/matériel
                op['employe_nom'] = op.get('declarant_nom') or op.get('employe_nom')
                # Service: si employe/service non liés, mettre 'Non spécifié'
                op['service_nom'] = op.get('service_nom') or 'Non spécifié'
                # Type matériel et modèle: afficher "Materiel (N° Série)"
                try:
                    type_mat = None
                    if op.get('actifs_json'):
                        actifs = json.loads(op['actifs_json'])
                        if isinstance(actifs, list) and len(actifs) > 0 and actifs[0]:
                            type_mat = actifs[0]
                    op['type_materiel'] = 'Incident'
                    # Colonne 'Matériel (Type - Modèle)' doit contenir Materiel(Num Série) pour incidents
                    mat_label = type_mat or 'Matériel'
                    serie_label = op.get('numero_serie_actif') or '-'
                    op['modele'] = f"{mat_label} ({serie_label})"
                except Exception:
                    op['type_materiel'] = 'Incident'
                    serie_label = op.get('numero_serie_actif') or '-'
                    op['modele'] = f"Matériel ({serie_label})"
                op['numero_serie'] = op.get('numero_serie_actif') or '-'
            else:
                # Pour les opérations, s'assurer que les champs sont présents
                op['declarant_nom'] = op.get('employe_nom')
                op['numero_serie_actif'] = op.get('numero_serie')
        
        return jsonify({'success': True, 'data': operations})
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'historique: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/operation/<int:operation_id>', methods=['GET'])
def get_operation_details(operation_id):
    """Récupérer les détails d'une opération (attribution/restitution)"""
    try:
        # Récupérer les détails de l'opération
        operation_query = """
            SELECT 
                o.*,
                e.nom as employe_nom,
                s.nom as service_nom,
                m.modele,
                m.numero_serie,
                tm.nom as type_materiel
            FROM operations o
            LEFT JOIN employes e ON o.employe_id = e.id
            LEFT JOIN services s ON e.service_id = s.id
            LEFT JOIN materiels m ON o.materiel_id = m.id
            LEFT JOIN types_materiel tm ON m.type_id = tm.id
            WHERE o.id = %s
        """
        operation = db.execute_query(operation_query, (operation_id,))
        
        if not operation:
            return jsonify({'success': False, 'error': 'Opération non trouvée'}), 404
        
        operation_data = operation[0]
        
        # Pour les opérations (attributions/restitutions), récupérer les signatures
        signatures_query = """
            SELECT type_signature, nom, fonction, date_signature, fichier_signature
            FROM signatures
            WHERE operation_id = %s
        """
        signatures = db.execute_query(signatures_query, (operation_id,))
        
        return jsonify({
            'success': True,
            'data': {
                'operation': operation_data,
                'signatures': signatures
            }
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des détails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/incident/<int:operation_id>', methods=['GET'])
def get_incident_details(operation_id):
    """Récupérer les détails d'un incident"""
    try:
        # Récupérer les détails de l'incident
        operation_query = """
            SELECT 
                o.*,
                e.nom as employe_nom,
                s.nom as service_nom,
                m.modele,
                m.numero_serie,
                tm.nom as type_materiel
            FROM operations o
            LEFT JOIN employes e ON o.employe_id = e.id
            LEFT JOIN services s ON e.service_id = s.id
            LEFT JOIN materiels m ON o.materiel_id = m.id
            LEFT JOIN types_materiel tm ON m.type_id = tm.id
            WHERE o.id = %s AND o.type_operation = 'incident'
        """
        operation = db.execute_query(operation_query, (operation_id,))
        
        if not operation:
            return jsonify({'success': False, 'error': 'Incident non trouvé'}), 404
        
        operation_data = operation[0]
        
        # Pour les incidents, parser les données JSON et renommer signature_png
        try:
            if operation_data.get('actifs_json'):
                operation_data['actifs'] = json.loads(operation_data['actifs_json'])
            if operation_data.get('natures_json'):
                operation_data['natures'] = json.loads(operation_data['natures_json'])
        except json.JSONDecodeError:
            operation_data['actifs'] = []
            operation_data['natures'] = []
        
        # Renommer signature_png en signature pour la cohérence
        if 'signature_png' in operation_data:
            operation_data['signature'] = operation_data.pop('signature_png')
        
        # S'assurer que la signature est incluse même si elle est null
        if 'signature' not in operation_data:
            operation_data['signature'] = None
        
        return jsonify({
            'success': True,
            'data': {
                'incident': operation_data
            }
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des détails de l'incident: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/incidents', methods=['POST'])
def create_incident():
    """Créer une fiche de signalisation d'incident"""
    try:
        data = request.get_json()

        # Champs minimaux
        required = ['declarant_nom', 'telephone']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Champ manquant: {field}'}), 400

        # Générer le numéro de fiche pour l'incident
        numero_fiche = generate_numero_fiche('incident')

        # Lier éventuellement l'incident à un employé (pour afficher le service dans l'historique)
        employe_id = None
        try:
            service_nom = data.get('service')
            if service_nom and data.get('declarant_nom'):
                service_rows = db.execute_query("SELECT id FROM services WHERE nom = %s", (service_nom,))
                if service_rows:
                    service_id = service_rows[0]['id']
                    emp_rows = db.execute_query(
                        "SELECT id FROM employes WHERE nom = %s AND service_id = %s",
                        (data.get('declarant_nom'), service_id)
                    )
                    if emp_rows:
                        employe_id = emp_rows[0]['id']
                    else:
                        ins = db.execute_query(
                            "INSERT INTO employes (nom, service_id) VALUES (%s, %s)",
                            (data.get('declarant_nom'), service_id)
                        )
                        if ins is not None:
                            employe_id = db.get_last_insert_id()
        except Exception as _e:
            logging.warning(f"Impossible de lier l'incident à un employé: {_e}")

        query = """
            INSERT INTO operations (
                numero_fiche, type_operation, date_operation, employe_id, declarant_nom, telephone, email, poste,
                numero_serie_actif, actifs_json, natures_json, autres_infos, signature_png
            ) VALUES (%s, 'incident', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            numero_fiche,
            data.get('date_incident'),
            employe_id,
            data.get('declarant_nom'),
            data.get('telephone'),
            data.get('email'),
            data.get('poste'),
            data.get('numero_serie_actif'),
            json.dumps([data.get('materiel_touche')] if data.get('materiel_touche') else [], ensure_ascii=False),
            json.dumps(data.get('natures', []), ensure_ascii=False),
            data.get('autres_infos'),
            data.get('signature_png')
        )

        rc = db.execute_query(query, params)
        if rc is None:
            raise Exception("Échec d'enregistrement de l'incident")
        incident_id = db.get_last_insert_id()
        
        return jsonify({'success': True, 'message': 'Incident enregistré', 'id': incident_id, 'numero_fiche': numero_fiche})

    except Exception as e:
        logging.error(f"Erreur lors de la création de l'incident: {e}")
        if current_app.config.get('DEBUG'):
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': "Une erreur interne est survenue. Merci de contacter l'administrateur."}), 500
