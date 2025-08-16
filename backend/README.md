# Gestion Matériel IT - Backend Python

Ce projet est un système de gestion de matériel informatique avec un backend Python/Flask et une base de données MySQL.

## Fonctionnalités

- ✅ **Attribution de matériel** : Enregistrement des attributions avec signatures
- ✅ **Restitution de matériel** : Gestion des restitutions
- ✅ **Historique complet** : Suivi de toutes les opérations
- ✅ **Export PDF** : Export de l'historique et des détails en PDF
- ✅ **Filtres avancés** : Recherche par employé, service, type de matériel, etc.
- ✅ **Interface moderne** : Design responsive et intuitif

## Prérequis

- Python 3.8+
- MySQL 8.0+
- pip (gestionnaire de paquets Python)

## Installation

### 1. Cloner le projet
```bash
git clone <url-du-projet>
cd materiel_app/backend
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Configuration de la base de données

#### Option A : Utiliser le script d'initialisation automatique
```bash
python init_db.py
```

#### Option B : Configuration manuelle
1. Créer une base de données MySQL nommée `materiel_it_db`
2. Exécuter le script SQL dans `database/schema.sql`

### 4. Configuration des variables d'environnement

Créer un fichier `.env` dans le dossier `backend` :
```env
# Configuration Base de données MySQL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=materiel_it_db
DB_PORT=3306

# Configuration Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=votre-cle-secrete-ici
```

## Démarrage

### 1. Démarrer le serveur Flask
```bash
python run.py
```

Le serveur sera accessible à l'adresse : `http://localhost:5000`

### 2. Accéder à l'application
- **Page d'accueil** : http://localhost:5000/
- **Attribution** : http://localhost:5000/attribution
- **Restitution** : http://localhost:5000/restitution
- **Historique** : http://localhost:5000/historique

## Structure du projet

```
backend/
├── app/
│   ├── __init__.py          # Configuration Flask
│   └── routes.py            # Routes API et pages
├── database/
│   ├── database.py          # Connexion MySQL
│   └── schema.sql           # Schéma de la base de données
├── config.py                # Configuration générale
├── run.py                   # Point d'entrée
├── init_db.py               # Script d'initialisation DB
├── requirements.txt         # Dépendances Python
└── README.md               # Ce fichier
```

## API Endpoints

### GET /api/services
Récupère la liste des services

### GET /api/types-materiel
Récupère la liste des types de matériel

### POST /api/attribution
Crée une nouvelle attribution

### POST /api/restitution
Crée une nouvelle restitution

### GET /api/historique
Récupère l'historique avec filtres optionnels :
- `employe` : Nom de l'employé
- `service` : Service
- `type_materiel` : Type de matériel
- `serie` : Numéro de série
- `date_debut` : Date de début
- `date_fin` : Date de fin

### GET /api/operation/{id}
Récupère les détails d'une opération

## Base de données

### Tables principales

- **services** : Services de l'entreprise
- **employes** : Employés
- **types_materiel** : Types de matériel
- **materiels** : Matériels
- **operations** : Opérations (attributions/restitutions)
- **signatures** : Signatures des opérations
- **utilisateurs** : Utilisateurs système

## Fonctionnalités avancées

### Export PDF
- Export de l'historique complet en PDF
- Export des détails d'une opération en PDF
- Capture de toute la page avec html2canvas

### Gestion des signatures
- Upload d'images de signatures
- Stockage en Base64 dans la base de données
- Affichage dans les détails des opérations

### Filtres et recherche
- Recherche par employé
- Filtrage par service
- Recherche par type de matériel
- Filtrage par numéro de série
- Filtrage par période

## Dépannage

### Erreur de connexion MySQL
1. Vérifier que MySQL est démarré
2. Vérifier les paramètres de connexion dans `.env`
3. Vérifier que l'utilisateur a les droits sur la base de données

### Erreur de dépendances Python
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Erreur de port déjà utilisé
Changer le port dans `run.py` :
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

## Support

Pour toute question ou problème, veuillez créer une issue dans le repository du projet.
