from flask import Blueprint, request, jsonify, render_template, send_from_directory
from database.database import db
import json
import logging
from datetime import datetime

# Blueprint pour les pages principales
main_bp = Blueprint('main', __name__)

# Blueprint pour l'API
api_bp = Blueprint('api', __name__)

@main_bp.route('/')
def index():
    """Page d'accueil - redirection vers attribution"""
    return send_from_directory('../templates', 'index.html')

@main_bp.route('/attribution')
def attribution():
    """Page d'attribution"""
    return send_from_directory('../templates', 'index.html')

@main_bp.route('/restitution')
def restitution():
    """Page de restitution"""
    return send_from_directory('../templates', 'restitution.html')

@main_bp.route('/historique')
def historique():
    """Page d'historique"""
    return send_from_directory('../templates', 'historique.html')

@main_bp.route('/css/<path:filename>')
def css(filename):
    """Servir les fichiers CSS"""
    return send_from_directory('../templates/css', filename)

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
        
        # Insérer l'employé s'il n'existe pas
        employe_query = """
            INSERT INTO employes (nom, service_id) 
            SELECT %s, s.id FROM services s WHERE s.nom = %s
            ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
        """
        db.execute_query(employe_query, (data['nom'], data['service']))
        employe_id = db.get_last_insert_id()
        
        # Traiter chaque matériel
        operations = []
        for materiel_data in data['materiels']:
            # Insérer le matériel s'il n'existe pas
            materiel_query = """
                INSERT INTO materiels (type_id, modele, numero_serie, service_achat, date_achat, statut)
                SELECT tm.id, %s, %s, %s, %s, 'attribue'
                FROM types_materiel tm WHERE tm.nom = %s
                ON DUPLICATE KEY UPDATE statut = 'attribue'
            """
            db.execute_query(materiel_query, (
                materiel_data['modele'],
                materiel_data['serie'],
                materiel_data.get('serviceAchat', ''),
                materiel_data.get('dateRemise'),
                materiel_data['type']
            ))
            materiel_id = db.get_last_insert_id()
            
            # Créer l'opération d'attribution
            operation_query = """
                INSERT INTO operations (type_operation, employe_id, materiel_id, date_operation, date_remise)
                VALUES ('attribution', %s, %s, %s, %s)
            """
            db.execute_query(operation_query, (
                employe_id,
                materiel_id,
                datetime.now().date(),
                materiel_data.get('dateRemise')
            ))
            operation_id = db.get_last_insert_id()
            operations.append(operation_id)
        
        # Insérer les signatures
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
        db.execute_many(signature_query, signatures_data)
        
        return jsonify({
            'success': True, 
            'message': 'Attribution créée avec succès',
            'operation_ids': operations
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la création de l'attribution: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/restitution', methods=['POST'])
def create_restitution():
    """Créer une nouvelle restitution"""
    try:
        data = request.get_json()
        
        # Vérifier les données requises
        required_fields = ['nom', 'service', 'materiels', 'redaction', 'validation', 'destinataire', 'signatures']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Champ manquant: {field}'}), 400
        
        # Récupérer l'employé
        employe_query = "SELECT id FROM employes WHERE nom = %s"
        employe_result = db.execute_query(employe_query, (data['nom'],))
        if not employe_result:
            return jsonify({'success': False, 'error': 'Employé non trouvé'}), 404
        
        employe_id = employe_result[0]['id']
        
        # Traiter chaque matériel
        operations = []
        for materiel_data in data['materiels']:
            # Récupérer le matériel
            materiel_query = "SELECT id FROM materiels WHERE numero_serie = %s"
            materiel_result = db.execute_query(materiel_query, (materiel_data['serie'],))
            if not materiel_result:
                return jsonify({'success': False, 'error': f'Matériel non trouvé: {materiel_data["serie"]}'}), 404
            
            materiel_id = materiel_result[0]['id']
            
            # Créer l'opération de restitution
            operation_query = """
                INSERT INTO operations (type_operation, employe_id, materiel_id, date_operation, date_restitution)
                VALUES ('restitution', %s, %s, %s, %s)
            """
            db.execute_query(operation_query, (
                employe_id,
                materiel_id,
                datetime.now().date(),
                materiel_data.get('dateRestitution')
            ))
            operation_id = db.get_last_insert_id()
            operations.append(operation_id)
            
            # Mettre à jour le statut du matériel
            update_materiel_query = "UPDATE materiels SET statut = 'disponible' WHERE id = %s"
            db.execute_query(update_materiel_query, (materiel_id,))
        
        # Insérer les signatures
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
        db.execute_many(signature_query, signatures_data)
        
        return jsonify({
            'success': True, 
            'message': 'Restitution créée avec succès',
            'operation_ids': operations
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la création de la restitution: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/historique', methods=['GET'])
def get_historique():
    """Récupérer l'historique des opérations avec filtres"""
    try:
        # Paramètres de filtrage
        employe = request.args.get('employe', '')
        service = request.args.get('service', '')
        type_materiel = request.args.get('type_materiel', '')
        serie = request.args.get('serie', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')
        
        # Construction de la requête
        query = """
            SELECT 
                o.id,
                o.type_operation,
                o.date_operation,
                o.date_remise,
                o.date_restitution,
                e.nom as employe_nom,
                s.nom as service_nom,
                m.modele,
                m.numero_serie,
                tm.nom as type_materiel
            FROM operations o
            JOIN employes e ON o.employe_id = e.id
            JOIN services s ON e.service_id = s.id
            JOIN materiels m ON o.materiel_id = m.id
            JOIN types_materiel tm ON m.type_id = tm.id
            WHERE 1=1
        """
        params = []
        
        if employe:
            query += " AND e.nom LIKE %s"
            params.append(f'%{employe}%')
        
        if service:
            query += " AND s.nom = %s"
            params.append(service)
        
        if type_materiel:
            query += " AND tm.nom LIKE %s"
            params.append(f'%{type_materiel}%')
        
        if serie:
            query += " AND m.numero_serie LIKE %s"
            params.append(f'%{serie}%')
        
        if date_debut:
            query += " AND o.date_operation >= %s"
            params.append(date_debut)
        
        if date_fin:
            query += " AND o.date_operation <= %s"
            params.append(date_fin)
        
        query += " ORDER BY o.date_operation DESC"
        
        operations = db.execute_query(query, params)
        
        return jsonify({'success': True, 'data': operations})
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'historique: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/operation/<int:operation_id>', methods=['GET'])
def get_operation_details(operation_id):
    """Récupérer les détails d'une opération"""
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
            JOIN employes e ON o.employe_id = e.id
            JOIN services s ON e.service_id = s.id
            JOIN materiels m ON o.materiel_id = m.id
            JOIN types_materiel tm ON m.type_id = tm.id
            WHERE o.id = %s
        """
        operation = db.execute_query(operation_query, (operation_id,))
        
        if not operation:
            return jsonify({'success': False, 'error': 'Opération non trouvée'}), 404
        
        # Récupérer les signatures
        signatures_query = """
            SELECT type_signature, nom, fonction, date_signature, fichier_signature
            FROM signatures
            WHERE operation_id = %s
        """
        signatures = db.execute_query(signatures_query, (operation_id,))
        
        return jsonify({
            'success': True,
            'data': {
                'operation': operation[0],
                'signatures': signatures
            }
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des détails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
