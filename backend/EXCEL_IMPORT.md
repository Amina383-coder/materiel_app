# Import de données depuis Excel

Ce guide explique comment importer des données depuis un fichier Excel vers la base de données MySQL.

## Structure du fichier Excel

Le fichier Excel doit contenir les feuilles suivantes :

### 1. Feuille "Services"
Colonnes requises :
- `nom` ou `Nom` : Nom du service
- `description` ou `Description` : Description du service (optionnel)

Exemple :
| nom | description |
|-----|-------------|
| Direction générale | Direction générale de l'entreprise |
| Informatique | Service informatique |
| Commercial | Service commercial |

### 2. Feuille "Employes"
Colonnes requises :
- `nom` ou `Nom` : Nom de l'employé
- `service` ou `Service` : Nom du service (doit correspondre à un service existant)
- `email` ou `Email` : Adresse email (optionnel)
- `telephone` ou `Telephone` : Numéro de téléphone (optionnel)

Exemple :
| nom | service | email | telephone |
|-----|---------|-------|-----------|
| Jean Dupont | Informatique | jean.dupont@entreprise.com | 0123456789 |
| Marie Martin | Commercial | marie.martin@entreprise.com | 0987654321 |

### 3. Feuille "Materiels"
Colonnes requises :
- `type` ou `Type` : Type de matériel (doit correspondre à un type existant)
- `modele` ou `Modele` : Modèle du matériel
- `numero_serie` ou `Numero_serie` : Numéro de série (unique)
- `service_achat` ou `Service_achat` : Service d'achat (optionnel)
- `date_achat` ou `Date_achat` : Date d'achat (optionnel)
- `statut` ou `Statut` : Statut du matériel (optionnel, défaut: 'disponible')

Exemple :
| type | modele | numero_serie | service_achat | date_achat | statut |
|------|--------|--------------|---------------|------------|--------|
| ordinateur_portable | Dell Latitude 5520 | SN123456789 | Informatique | 2023-01-15 | disponible |
| ecran | Dell 24" | SN987654321 | Informatique | 2023-02-20 | disponible |

## Types de matériel disponibles

Les types de matériel suivants sont pré-configurés dans la base de données :
- `ordinateur_portable` : Ordinateur portable
- `ordinateur_bureau` : Ordinateur de bureau
- `ecran` : Écran d'ordinateur
- `telephone` : Téléphone
- `tablette` : Tablette tactile
- `accessoires` : Accessoires informatiques

## Utilisation du script d'import

### 1. Préparer le fichier Excel
Créez votre fichier Excel avec les feuilles et colonnes appropriées.

### 2. Exécuter le script d'import
```bash
cd backend
python import_excel.py votre_fichier.xlsx
```

### 3. Vérifier l'import
Le script affichera les informations d'import pour chaque entité :
```
=== Import de données depuis Excel ===
Fichier: donnees.xlsx

Feuilles disponibles: ['Services', 'Employes', 'Materiels']

Import des services...
Service importé: Direction générale
Service importé: Informatique
✅ Services importés avec succès

Import des employés...
Employé importé: Jean Dupont - Informatique
Employé importé: Marie Martin - Commercial
✅ Employés importés avec succès

Import des matériels...
Matériel importé: ordinateur_portable - Dell Latitude 5520 - SN123456789
Matériel importé: ecran - Dell 24" - SN987654321
✅ Matériels importés avec succès

=== Import terminé ===
```

## Gestion des erreurs

### Erreurs courantes

1. **Service non trouvé** : Le service spécifié dans la feuille "Employes" n'existe pas
   - Solution : Vérifiez que le service existe dans la feuille "Services"

2. **Type de matériel non trouvé** : Le type spécifié dans la feuille "Materiels" n'existe pas
   - Solution : Utilisez un des types pré-configurés

3. **Numéro de série en double** : Un numéro de série est déjà utilisé
   - Solution : Vérifiez l'unicité des numéros de série

4. **Format de date incorrect** : Les dates doivent être au format YYYY-MM-DD
   - Solution : Corrigez le format des dates dans Excel

### Logs d'erreur

Le script affiche les erreurs dans la console. En cas de problème, vérifiez :
- La connexion à la base de données
- Les permissions de l'utilisateur MySQL
- Le format des données dans Excel

## Exemple de fichier Excel complet

Vous pouvez télécharger un exemple de fichier Excel avec la structure correcte depuis le repository du projet.

## Support

Pour toute question concernant l'import Excel, veuillez créer une issue dans le repository du projet.
