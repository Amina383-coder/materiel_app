#!/usr/bin/env python3
"""
Script d'import de données depuis un fichier Excel
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
from config import Config
import logging
import sys
import os

def connect_to_database():
    """Connexion à la base de données"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT
        )
        return connection
    except Error as e:
        logging.error(f"Erreur de connexion à la base de données: {e}")
        return None

def import_services_from_excel(file_path, sheet_name='Services'):
    """Importer les services depuis Excel"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        connection = connect_to_database()
        
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        for index, row in df.iterrows():
            nom = row.get('nom', row.get('Nom', ''))
            description = row.get('description', row.get('Description', ''))
            
            if nom:
                query = """
                    INSERT INTO services (nom, description) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE description = VALUES(description)
                """
                cursor.execute(query, (nom, description))
                print(f"Service importé: {nom}")
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de l'import des services: {e}")
        return False

def import_employes_from_excel(file_path, sheet_name='Employes'):
    """Importer les employés depuis Excel"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        connection = connect_to_database()
        
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        for index, row in df.iterrows():
            nom = row.get('nom', row.get('Nom', ''))
            service = row.get('service', row.get('Service', ''))
            email = row.get('email', row.get('Email', ''))
            telephone = row.get('telephone', row.get('Telephone', ''))
            
            if nom and service:
                # Récupérer l'ID du service
                service_query = "SELECT id FROM services WHERE nom = %s"
                cursor.execute(service_query, (service,))
                service_result = cursor.fetchone()
                
                if service_result:
                    service_id = service_result[0]
                    
                    query = """
                        INSERT INTO employes (nom, service_id, email, telephone) 
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        service_id = VALUES(service_id),
                        email = VALUES(email),
                        telephone = VALUES(telephone)
                    """
                    cursor.execute(query, (nom, service_id, email, telephone))
                    print(f"Employé importé: {nom} - {service}")
                else:
                    print(f"Service non trouvé: {service}")
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de l'import des employés: {e}")
        return False

def import_materiels_from_excel(file_path, sheet_name='Materiels'):
    """Importer les matériels depuis Excel"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        connection = connect_to_database()
        
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        for index, row in df.iterrows():
            type_materiel = row.get('type', row.get('Type', ''))
            modele = row.get('modele', row.get('Modele', ''))
            numero_serie = row.get('numero_serie', row.get('Numero_serie', ''))
            service_achat = row.get('service_achat', row.get('Service_achat', ''))
            date_achat = row.get('date_achat', row.get('Date_achat', ''))
            statut = row.get('statut', row.get('Statut', 'disponible'))
            
            if type_materiel and modele and numero_serie:
                # Récupérer l'ID du type de matériel
                type_query = "SELECT id FROM types_materiel WHERE nom = %s"
                cursor.execute(type_query, (type_materiel,))
                type_result = cursor.fetchone()
                
                if type_result:
                    type_id = type_result[0]
                    
                    query = """
                        INSERT INTO materiels (type_id, modele, numero_serie, service_achat, date_achat, statut) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        modele = VALUES(modele),
                        service_achat = VALUES(service_achat),
                        date_achat = VALUES(date_achat),
                        statut = VALUES(statut)
                    """
                    cursor.execute(query, (type_id, modele, numero_serie, service_achat, date_achat, statut))
                    print(f"Matériel importé: {type_materiel} - {modele} - {numero_serie}")
                else:
                    print(f"Type de matériel non trouvé: {type_materiel}")
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de l'import des matériels: {e}")
        return False

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python import_excel.py <fichier_excel>")
        print("Exemple: python import_excel.py donnees.xlsx")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Fichier non trouvé: {file_path}")
        return
    
    print("=== Import de données depuis Excel ===")
    print(f"Fichier: {file_path}")
    print()
    
    # Lire les noms des feuilles
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"Feuilles disponibles: {excel_file.sheet_names}")
        print()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel: {e}")
        return
    
    # Importer les services
    if 'Services' in excel_file.sheet_names:
        print("Import des services...")
        if import_services_from_excel(file_path):
            print("✅ Services importés avec succès")
        else:
            print("❌ Erreur lors de l'import des services")
        print()
    
    # Importer les employés
    if 'Employes' in excel_file.sheet_names:
        print("Import des employés...")
        if import_employes_from_excel(file_path):
            print("✅ Employés importés avec succès")
        else:
            print("❌ Erreur lors de l'import des employés")
        print()
    
    # Importer les matériels
    if 'Materiels' in excel_file.sheet_names:
        print("Import des matériels...")
        if import_materiels_from_excel(file_path):
            print("✅ Matériels importés avec succès")
        else:
            print("❌ Erreur lors de l'import des matériels")
        print()
    
    print("=== Import terminé ===")

if __name__ == "__main__":
    main()
