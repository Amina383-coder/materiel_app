#!/usr/bin/env python3
"""
Script d'initialisation de la base de données MySQL
"""

import mysql.connector
from mysql.connector import Error
import os
from config import Config

def create_database():
    """Créer la base de données et les tables"""
    try:
        # Connexion à MySQL sans spécifier de base de données
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Créer la base de données
            print("Création de la base de données...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Base de données '{Config.DB_NAME}' créée avec succès")
            
            # Utiliser la base de données
            cursor.execute(f"USE {Config.DB_NAME}")
            
            # Lire et exécuter le script SQL pour les tables
            print("Création des tables...")
            with open('database/tables.sql', 'r', encoding='utf-8') as file:
                sql_commands = file.read()
                
            # Diviser les commandes SQL
            commands = sql_commands.split(';')
            
            for command in commands:
                command = command.strip()
                if command and not command.startswith('--'):
                    try:
                        cursor.execute(command)
                        print(f"Commande exécutée: {command[:50]}...")
                    except Error as e:
                        if "already exists" not in str(e).lower():
                            print(f"Erreur lors de l'exécution: {e}")
            
            connection.commit()
            print("Base de données initialisée avec succès!")
            
    except Error as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Connexion MySQL fermée")

if __name__ == "__main__":
    print("=== Initialisation de la base de données MySQL ===")
    create_database()
