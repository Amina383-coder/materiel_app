import mysql.connector
from mysql.connector import Error
from config import Config
import logging

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Établir la connexion à la base de données MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
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
    
    def execute_query(self, query, params=None):
        """Exécuter une requête SQL"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
                
        except Error as e:
            logging.error(f"Erreur d'exécution de requête: {e}")
            self.connection.rollback()
            return None
    
    def execute_many(self, query, params_list):
        """Exécuter plusieurs requêtes SQL"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return self.cursor.rowcount
            
        except Error as e:
            logging.error(f"Erreur d'exécution multiple: {e}")
            self.connection.rollback()
            return None
    
    def get_last_insert_id(self):
        """Obtenir l'ID de la dernière insertion"""
        return self.cursor.lastrowid if self.cursor else None

# Instance globale de la base de données
db = Database()
