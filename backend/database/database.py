import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import logging

# Charger .env
load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Établir la connexion à la base de données MySQL"""
        try:
            # Normaliser le mot de passe si valeur d'exemple
            raw_password = os.getenv("DB_PASSWORD", "")
            if raw_password in ("votre_mot_de_passe_mysql", "your_mysql_password", "votre-mot-de-passe", "changeme"):
                raw_password = ""

            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=raw_password,
                database=os.getenv("DB_NAME"),
                port=int(os.getenv("DB_PORT", 3306)),
                charset='utf8mb4'
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logging.info("Connexion à MySQL réussie")
                return True
                
        except Error as e:
            logging.error(f"Erreur de connexion à MySQL: {e}")
            return False
    
    def disconnect(self):
        """Fermer la connexion à la base de données"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Connexion MySQL fermée")
        self.connection = None
        self.cursor = None
    
    def execute_query(self, query, params=None):
        """Exécuter une requête SQL"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            if not self.cursor:
                logging.error("Curseur MySQL indisponible (connexion échouée)")
                return None
            
            self.cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
                
        except Exception as e:
            logging.error(f"Erreur d'exécution de requête: {e}")
            try:
                if self.connection and self.connection.is_connected():
                    self.connection.rollback()
            except Exception:
                pass
            return None
    
    def execute_many(self, query, params_list):
        """Exécuter plusieurs requêtes SQL"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            if not self.cursor:
                logging.error("Curseur MySQL indisponible (connexion échouée)")
                return None
            
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return self.cursor.rowcount
            
        except Exception as e:
            logging.error(f"Erreur d'exécution multiple: {e}")
            try:
                if self.connection and self.connection.is_connected():
                    self.connection.rollback()
            except Exception:
                pass
            return None
    
    def get_last_insert_id(self):
        """Obtenir l'ID de la dernière insertion"""
        return self.cursor.lastrowid if self.cursor else None

# Instance globale de la base de données
db = Database()
