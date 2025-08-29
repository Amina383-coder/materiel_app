-- Table des services
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table des employés
CREATE TABLE IF NOT EXISTS employes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    service_id INT,
    email VARCHAR(100),
    telephone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL
);

-- Table des types de matériel
CREATE TABLE IF NOT EXISTS types_materiel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des matériels
CREATE TABLE IF NOT EXISTS materiels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_id INT NOT NULL,
    modele VARCHAR(100) NOT NULL,
    numero_serie VARCHAR(100) UNIQUE NOT NULL,
    service_achat VARCHAR(100),
    date_achat DATE,
    statut ENUM('disponible', 'attribue', 'en_maintenance', 'retire') DEFAULT 'disponible',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES types_materiel(id) ON DELETE RESTRICT
);

-- Table des opérations unifiée (attributions, restitutions et incidents)
CREATE TABLE IF NOT EXISTS operations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_fiche VARCHAR(50),
    type_operation ENUM('attribution', 'restitution', 'incident') NOT NULL,
    employe_id INT,
    materiel_id INT,
    date_operation DATE NOT NULL,
    date_remise DATE,
    date_restitution DATE,
    motif TEXT,
    -- Champs spécifiques aux incidents
    declarant_nom VARCHAR(150),
    telephone VARCHAR(50),
    email VARCHAR(150),
    poste VARCHAR(150),
    numero_serie_actif VARCHAR(150),
    actifs_json LONGTEXT,
    natures_json LONGTEXT,
    autres_infos TEXT,
    signature_png LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE SET NULL,
    FOREIGN KEY (materiel_id) REFERENCES materiels(id) ON DELETE SET NULL
);

-- Table des signatures
CREATE TABLE IF NOT EXISTS signatures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT NOT NULL,
    type_signature ENUM('redaction', 'validation', 'destinataire') NOT NULL,
    nom VARCHAR(100) NOT NULL,
    fonction VARCHAR(100) NOT NULL,
    date_signature DATE NOT NULL,
    fichier_signature LONGTEXT, -- Base64 de l'image
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operation_id) REFERENCES operations(id) ON DELETE CASCADE
);

-- Table des utilisateurs système
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_utilisateur VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user', 'manager') DEFAULT 'user',
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insertion des données de base
INSERT IGNORE INTO services (nom, description) VALUES
('Direction générale', 'Direction générale de l\'entreprise'),
('Maintenance', 'Service de maintenance'),
('Contrôle de gestion', 'Service de contrôle de gestion'),
('Finance et comptabilité', 'Service financier et comptable'),
('Performance', 'Service performance'),
('Supply chain', 'Service supply chain'),
('QHSE', 'Service Qualité, Hygiène, Sécurité, Environnement'),
('Technique', 'Service technique'),
('Planification', 'Service de planification'),
('Informatique', 'Service informatique'),
('Recouvrement', 'Service de recouvrement'),
('Commercial', 'Service commercial');

INSERT IGNORE INTO types_materiel (nom, description) VALUES
('ordinateur_portable', 'Ordinateur portable'),
('ordinateur_bureau', 'Ordinateur de bureau'),
('ecran', 'Écran d\'ordinateur'),
('telephone', 'Téléphone'),
('tablette', 'Tablette tactile'),
('accessoires', 'Accessoires informatiques');

-- Index pour optimiser les performances
CREATE INDEX idx_operations_date ON operations(date_operation);
CREATE INDEX idx_operations_type ON operations(type_operation);
CREATE INDEX idx_materiels_serie ON materiels(numero_serie);
CREATE INDEX idx_materiels_statut ON materiels(statut);
CREATE INDEX idx_employes_service ON employes(service_id);