# TrainNomad Guide API

Serveur Go pour l'API des guides de destinations.

## Structure

```
guide/
├── main.go          # Point d'entrée serveur
├── api.go           # Endpoints HTTP
├── data.go          # Structures et chargement binaire
├── build_guides.py  # Script de construction du binaire
├── guides.json      # Source des données (généré)
├── guides.bin.gz    # Données binaires compressées
└── Dockerfile
```

## API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Statut du serveur |
| GET | `/guides` | Liste des guides (filtrable) |
| GET | `/guides/{slug}` | Détail d'un guide |
| GET | `/countries` | Liste des pays |

### Filtres `/guides`

- `?country=France` - Filtrer par pays
- `?search=paris` - Recherche textuelle
- `?featured=true` - Guides mis en avant uniquement

## Développement

### Prérequis

- Go 1.21+
- Python 3.10+ (pour build_guides.py)

### Générer les données

```bash
# Créer guides.json avec des exemples
python build_guides.py --sample

# Compiler en binaire
python build_guides.py -i guides.json -o guides.bin.gz
```

### Lancer le serveur

```bash
go run .
# ou
go build -o guide-server && ./guide-server
```

Le serveur démarre sur le port 8001 par défaut (configurable via `PORT`).

## Format binaire

Format `TNGDE001` (TrainNomad Guide Data Export v1):

```
Header:  "TNGDE001" (8 bytes) + nsections (4 bytes) + padding (4 bytes)
Section: name (24 bytes) + dtype (1 byte) + padding (7 bytes) + count (8 bytes) + size (8 bytes) + data
```

Sections:
- `meta` : JSON des métadonnées
- `guides` : JSON array des guides complets

## Déploiement

### Docker

```bash
docker build -t trainnomad-guide .
docker run -p 8001:8001 trainnomad-guide
```

### Render

Le fichier `Procfile` est inclus pour déploiement sur Render.

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `PORT` | 8001 | Port d'écoute |
| `GUIDES_PATH` | guides.bin.gz | Chemin du fichier de données |
