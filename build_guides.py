#!/usr/bin/env python3
"""
build_guides.py - Scanne les dossiers de pays et genere index.json

Structure attendue:
resultats_guides/
├── France/
│   ├── lyon.json
│   └── angers.json
├── Portugal/
│   └── lisbonne.json
└── index.json (genere automatiquement)

Usage:
    python build_guides.py                    # Scanne resultats_guides/
    python build_guides.py -d /chemin/custom  # Scanne un dossier custom
"""

import json
import argparse
from datetime import datetime
from pathlib import Path


def scan_guides_directory(guides_dir: str = 'resultats_guides'):
    """Scanne les dossiers par pays et retourne tous les guides."""

    guides_path = Path(guides_dir)

    if not guides_path.exists():
        print(f"Erreur: {guides_dir} n'existe pas")
        return []

    guides = []

    # Parcourir tous les dossiers de pays
    for country_dir in sorted(guides_path.iterdir()):
        if not country_dir.is_dir() or country_dir.name.startswith('.'):
            continue

        country_name = country_dir.name
        print(f"\nPays: {country_name}")

        # Parcourir tous les fichiers .json dans le dossier du pays
        for guide_file in sorted(country_dir.glob('*.json')):
            try:
                with open(guide_file, 'r', encoding='utf-8') as f:
                    guide_data = json.load(f)

                # Verifier que c'est un guide valide
                if 'slug' not in guide_data or 'name' not in guide_data:
                    print(f"  [SKIP] {guide_file.name} - pas de 'slug' ou 'name'")
                    continue

                # Compter les photo_spots
                photo_count = len(guide_data.get('photo_spots', []))

                # Ajouter le guide
                guides.append({
                    'slug': guide_data['slug'],
                    'name': guide_data['name'],
                    'country': country_name,
                    'path': f"/{guide_data['slug']}.json",  # Chemin relatif depuis le pays
                    'featured': guide_data.get('featured', False),
                    'file': str(guide_file.relative_to(guides_path))
                })

                print(f"  [OK] {guide_data['slug']}.json ({photo_count} photo_spots)")

            except json.JSONDecodeError as e:
                print(f"  [ERREUR] {guide_file.name} - JSON invalide: {e}")
            except Exception as e:
                print(f"  [ERREUR] {guide_file.name} - {e}")

    return guides


def generate_index(guides: list, guides_dir: str = 'resultats_guides'):
    """Genere le fichier index.json."""

    index = {
        "version": 1,
        "built_at": datetime.now().isoformat(),
        "guides": []
    }

    # Trier par pays puis par nom
    sorted_guides = sorted(guides, key=lambda g: (g['country'], g['name']))

    for guide in sorted_guides:
        index["guides"].append({
            "slug": guide['slug'],
            "name": guide['name'],
            "country": guide['country'],
            "path": guide['file'],  # Chemin complet depuis resultats_guides
            "featured": guide['featured']
        })

    # Sauvegarder l'index
    index_path = Path(guides_dir) / "index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Index genere: {index_path}")
    print(f"[OK] {len(guides)} guides trouves")

    return index


def main():
    parser = argparse.ArgumentParser(
        description='Scanne les dossiers de pays et genere index.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemple:
  python build_guides.py                    # Scanne resultats_guides/
  python build_guides.py -d ./guides/       # Scanne ./guides/

Structure attendue:
  resultats_guides/
  ├── France/
  │   ├── lyon.json
  │   └── angers.json
  ├── Espagne/
  │   └── barcelone.json
  └── index.json (genere automatiquement)
        """
    )
    parser.add_argument(
        '-d', '--dir',
        default='resultats_guides',
        help='Repertoire a scanner (defaut: resultats_guides)'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Scanning guides directory...")
    print("=" * 60)

    # Scanner les guides
    guides = scan_guides_directory(args.dir)

    if not guides:
        print("\n[ERREUR] Aucun guide trouve!")
        return

    # Generer l'index
    print("\n" + "=" * 60)
    print("Generating index...")
    print("=" * 60)

    generate_index(guides, args.dir)

    print("\n" + "=" * 60)
    print("Fait! index.json est a jour.")
    print("=" * 60)


if __name__ == '__main__':
    main()
