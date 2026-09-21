#!/usr/bin/env python3
"""
build_guides.py - Construit le fichier guides.bin.gz à partir de guides.json

Format binaire TNGDE001:
- Header: "TNGDE001" (8 bytes) + nsections (4 bytes) + padding (4 bytes)
- Sections: chaque section a un header de 48 bytes + données alignées sur 8 bytes

Usage:
    python build_guides.py
    python build_guides.py --input guides.json --output guides.bin.gz
"""

import json
import struct
import gzip
import argparse
from datetime import datetime
from pathlib import Path


def write_section(sections: list, name: str, dtype: int, data: bytes):
    """Ajoute une section au fichier binaire."""
    # Header: name (24 bytes) + dtype (1 byte) + padding (7 bytes) + count (8 bytes) + size (8 bytes)
    name_bytes = name.encode('utf-8')[:24].ljust(24, b'\x00')
    count = len(data) if dtype == 1 else len(data) // (1 << (dtype - 1))
    header = name_bytes + struct.pack('<B', dtype) + b'\x00' * 7 + struct.pack('<QQ', count, len(data))

    # Alignement sur 8 bytes
    padding = (8 - len(data) % 8) % 8
    sections.append(header + data + b'\x00' * padding)


def build_guides_bin(guides_data: dict, output_path: str):
    """Construit le fichier binaire."""

    meta = {
        "version": 1,
        "built_at": datetime.now().isoformat(),
        "num_guides": len(guides_data["guides"])
    }

    sections = []

    # Section meta (JSON)
    meta_json = json.dumps(meta, ensure_ascii=False).encode('utf-8')
    write_section(sections, "meta", 1, meta_json)

    # Section guides (JSON array)
    guides_json = json.dumps(guides_data["guides"], ensure_ascii=False).encode('utf-8')
    write_section(sections, "guides", 1, guides_json)

    # Construction du fichier final
    header = b"TNGDE001" + struct.pack('<I', len(sections)) + b'\x00' * 4
    content = header + b''.join(sections)

    # Compression gzip
    if output_path.endswith('.gz'):
        with gzip.open(output_path, 'wb') as f:
            f.write(content)
    else:
        with open(output_path, 'wb') as f:
            f.write(content)

    print(f"Fichier {output_path} créé: {len(guides_data['guides'])} guides, {len(content)} bytes")


def add_photo_spots(guides_data: dict):
    """Ajoute les photo_spots à chaque guide basé sur sa destination."""

    photo_spots_by_city = {
        "lisbonne": [
            {
                "name": "Miradouro de Santa Luzia",
                "description": "Belvédère emblématique d'Alfama avec vue sur le Tage et les toits aux tuiles ocres",
                "type": "viewpoint",
                "km_from_paris": 1700,
                "lat": 38.7136,
                "lon": -9.1308,
                "best_side": "sunrise"
            },
            {
                "name": "Praça do Comércio",
                "description": "La place royale ouverte sur le Tage. Architecture pombaline et ambiance majestueuse",
                "type": "plaza",
                "km_from_paris": 1700,
                "lat": 38.7071,
                "lon": -9.1365,
                "best_side": "afternoon"
            },
            {
                "name": "Pont 25 de Abril",
                "description": "Le \"Golden Gate\" portugais au coucher du soleil depuis le Cristo Rei ou Almada",
                "type": "bridge",
                "km_from_paris": 1700,
                "lat": 38.6912,
                "lon": -9.1772,
                "best_side": "sunset"
            }
        ],
        "barcelone": [
            {
                "name": "Sagrada Familia",
                "description": "Chef-d'œuvre architectural de Gaudí, la basilique la plus emblématique de Barcelone",
                "type": "church",
                "km_from_paris": 800,
                "lat": 41.4036,
                "lon": 2.1744,
                "best_side": "morning"
            },
            {
                "name": "Park Güell",
                "description": "Jardin spectaculaire dominant la ville avec mosaïques colorées et vues panoramiques",
                "type": "park",
                "km_from_paris": 800,
                "lat": 41.4145,
                "lon": 2.1526,
                "best_side": "afternoon"
            },
            {
                "name": "Montjuïc",
                "description": "Colline offrant des vues sur la ville, le port et les Montagnes de Montserrat",
                "type": "viewpoint",
                "km_from_paris": 800,
                "lat": 41.3694,
                "lon": 2.1769,
                "best_side": "sunset"
            }
        ],
        "lyon": [
            {
                "name": "Basilique de Notre-Dame de Fourvière",
                "description": "Basilique blanche dominant Lyon depuis la Fourvière, accès par funiculaire",
                "type": "church",
                "km_from_paris": 470,
                "lat": 45.7597,
                "lon": 4.8164,
                "best_side": "morning"
            },
            {
                "name": "Confluence - Musée des Confluences",
                "description": "Musée futuriste sur la péninsule de la Confluence avec architecture spectaculaire",
                "type": "museum",
                "km_from_paris": 470,
                "lat": 45.7219,
                "lon": 4.8166,
                "best_side": "afternoon"
            },
            {
                "name": "Parc de la Tête d'Or",
                "description": "Parc urbain avec lac, promenade et musées en cœur de ville",
                "type": "park",
                "km_from_paris": 470,
                "lat": 45.7740,
                "lon": 4.8398,
                "best_side": "morning"
            }
        ],
        "amsterdam": [
            {
                "name": "Canal Ring",
                "description": "Les canaux concentriques de Amsterdam avec maisons historiques et ponts pittoresques",
                "type": "waterway",
                "km_from_paris": 500,
                "lat": 52.3702,
                "lon": 4.8952,
                "best_side": "morning"
            },
            {
                "name": "Anne Frank House",
                "description": "Maison historique cachette d'Anne Frank pendant la Seconde Guerre mondiale",
                "type": "museum",
                "km_from_paris": 500,
                "lat": 52.3752,
                "lon": 4.8839,
                "best_side": "afternoon"
            },
            {
                "name": "Dam Square",
                "description": "Cœur historique d'Amsterdam avec le Palais Royal et le Monument National",
                "type": "plaza",
                "km_from_paris": 500,
                "lat": 52.3740,
                "lon": 4.8896,
                "best_side": "sunset"
            }
        ],
        "berlin": [
            {
                "name": "Porte de Brandebourg",
                "description": "Monument iconique symbolisant la réunification de Berlin",
                "type": "monument",
                "km_from_paris": 1000,
                "lat": 52.5163,
                "lon": 13.3777,
                "best_side": "afternoon"
            },
            {
                "name": "Mur de Berlin - East Side Gallery",
                "description": "Galerie à ciel ouvert sur le plus long tronçon du Mur de Berlin",
                "type": "museum",
                "km_from_paris": 1000,
                "lat": 52.5050,
                "lon": 13.4420,
                "best_side": "morning"
            },
            {
                "name": "Reichstag",
                "description": "Siège du Bundestag avec dôme de verre offrant une vue panoramique",
                "type": "building",
                "km_from_paris": 1000,
                "lat": 52.5186,
                "lon": 13.3755,
                "best_side": "sunset"
            }
        ],
        "bruxelles": [
            {
                "name": "Grand-Place",
                "description": "Place historique UNESCO entourée de guildes gothiques et baroques",
                "type": "plaza",
                "km_from_paris": 300,
                "lat": 50.8503,
                "lon": 4.3517,
                "best_side": "evening"
            },
            {
                "name": "Atomium",
                "description": "Monument futuriste en forme de molécule, symbole de Bruxelles",
                "type": "monument",
                "km_from_paris": 300,
                "lat": 50.8945,
                "lon": 4.3361,
                "best_side": "afternoon"
            },
            {
                "name": "Manneken Pis",
                "description": "Statue iconique de petit garçon urinant, symbole humoristique bruxellois",
                "type": "statue",
                "km_from_paris": 300,
                "lat": 50.8461,
                "lon": 4.3516,
                "best_side": "morning"
            }
        ],
        "milan": [
            {
                "name": "Duomo de Milan",
                "description": "Cathédrale gothique majestueuse, chef-d'œuvre architectural du style gothic tardif",
                "type": "church",
                "km_from_paris": 850,
                "lat": 45.4642,
                "lon": 9.1900,
                "best_side": "morning"
            },
            {
                "name": "La Scala",
                "description": "Opéra renommé mondialement, architecture élégante du XVIIIe siècle",
                "type": "theater",
                "km_from_paris": 850,
                "lat": 45.4683,
                "lon": 9.1917,
                "best_side": "evening"
            },
            {
                "name": "Navigli",
                "description": "Canaux historiques avec bars et restaurants branché, atmosphère bohème",
                "type": "waterway",
                "km_from_paris": 850,
                "lat": 45.4563,
                "lon": 9.1849,
                "best_side": "sunset"
            }
        ],
        "angers": [
            {
                "name": "Château d'Angers",
                "description": "Forteresse massive du XIIIe siècle avec jardins, tapisserie de l'Apocalypse",
                "type": "castle",
                "km_from_paris": 290,
                "lat": 47.4691,
                "lon": -0.5520,
                "best_side": "morning"
            },
            {
                "name": "Cathédrale Saint-Maurice",
                "description": "Splendide cathédrale gothique avec vitraux remarquables",
                "type": "church",
                "km_from_paris": 290,
                "lat": 47.4748,
                "lon": -0.5546,
                "best_side": "afternoon"
            },
            {
                "name": "Confluence - Musée des Confluences d'Angers",
                "description": "Musée moderne d'art contemporain et patrimoine, architecture audacieuse",
                "type": "museum",
                "km_from_paris": 290,
                "lat": 47.4627,
                "lon": -0.5597,
                "best_side": "afternoon"
            }
        ]
    }

    # Ajouter les photo_spots à chaque guide
    for guide in guides_data["guides"]:
        slug = guide["slug"]
        if slug in photo_spots_by_city:
            guide["photo_spots"] = photo_spots_by_city[slug]

    return guides_data


def create_sample_guides():
    """Crée un fichier guides.json exemple avec quelques destinations."""

    guides = {
        "guides": [
            {
                "slug": "lisbonne",
                "name": "Lisbonne",
                "country": "Portugal",
                "country_code": "PT",
                "image": "/assets/guides/lisbonne-cover.webp",
                "hero_image": "/assets/guides/lisbonne-hero.webp",
                "description": "La capitale portugaise la plus attachante. Fado, Alfama et pastéis de nata au bout du rail.",
                "reading_time": 12,
                "featured": True,
                "featured_title": "Fado, Alfama et pastéis de nata au bout du rail",
                "featured_subtitle": "La capitale européenne la plus attachante, accessible en train de nuit depuis Paris.",
                "tags": ["Train de nuit", "Culture", "Gastronomie"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "~24h (nuit)"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Modéré"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Méditerranéen"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Gare de Santa Apolónia",
                        "icon": "fa-train",
                        "content": "<p>Santa Apolónia est la gare historique de Lisbonne, terminus des trains internationaux. Située sur les rives du Tage, elle offre un accès direct au quartier d'Alfama.</p>"
                    },
                    {
                        "id": "quartiers",
                        "title": "Quartiers à explorer",
                        "icon": "fa-map-location-dot",
                        "content": "<p><strong>Alfama</strong> : le plus ancien quartier, ruelles médiévales et fado. <strong>Baixa</strong> : centre reconstruit après le séisme de 1755. <strong>Belém</strong> : monastère des Hiéronymites et pastéis de nata.</p>"
                    }
                ]
            },
            {
                "slug": "angers",
                "name": "Angers",
                "country": "France",
                "country_code": "FR",
                "image": "/assets/guides/angers-cover.webp",
                "hero_image": "/assets/guides/angers-hero.webp",
                "description": "Capitale de l'Anjou, ville d'art et d'histoire au bord de la Maine.",
                "reading_time": 8,
                "featured": False,
                "tags": ["TGV", "Patrimoine", "Vin"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "1h30"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Modéré"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Océanique"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Gare d'Angers Saint-Laud",
                        "icon": "fa-train",
                        "content": "<p>Gare centrale desservie par TGV. WiFi gratuit, nombreuses prises électriques dans l'espace d'attente.</p>"
                    },
                    {
                        "id": "coworking",
                        "title": "Espaces de travail",
                        "icon": "fa-laptop",
                        "content": "<p><strong>La Cantine Numérique</strong> : coworking central à 10 min de la gare, journée à 15€. <strong>Café Pinson</strong> : laptop-friendly, WiFi rapide.</p>"
                    }
                ]
            },
            {
                "slug": "barcelone",
                "name": "Barcelone",
                "country": "Espagne",
                "country_code": "ES",
                "image": "/assets/guides/barcelone-cover.webp",
                "hero_image": "/assets/guides/barcelone-hero.webp",
                "description": "Capitale catalane vibrante. Gaudí, plages et tapas accessible en TGV.",
                "reading_time": 14,
                "featured": False,
                "tags": ["AVE", "Plage", "Architecture"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "6h30"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Modéré"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Méditerranéen"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Barcelona Sants",
                        "icon": "fa-train",
                        "content": "<p>Hub ferroviaire principal. TGV depuis Paris, AVE depuis Madrid. Prévoir 20min pour le contrôle aux frontières à Figueres.</p>"
                    },
                    {
                        "id": "coworking",
                        "title": "Espaces de travail",
                        "icon": "fa-laptop",
                        "content": "<p><strong>Betahaus</strong> : le plus célèbre coworking de Barcelone, quartier Gràcia. <strong>OneCoWork</strong> : plusieurs emplacements dont un face à la plage.</p>"
                    }
                ]
            },
            {
                "slug": "lyon",
                "name": "Lyon",
                "country": "France",
                "country_code": "FR",
                "image": "/assets/guides/lyon-cover.webp",
                "hero_image": "/assets/guides/lyon-hero.webp",
                "description": "Capitale gastronomique, entre Rhône et Saône. Bouchons, traboules et tech.",
                "reading_time": 11,
                "featured": False,
                "tags": ["TGV", "Gastronomie", "Tech Hub"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "2h"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Modéré-élevé"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Continental"}
                ],
                "sections": [
                    {
                        "id": "gares",
                        "title": "Les gares de Lyon",
                        "icon": "fa-train",
                        "content": "<p><strong>Lyon Part-Dieu</strong> : la plus grande gare TGV hors Paris. <strong>Lyon Perrache</strong> : gare historique en centre-ville.</p>"
                    },
                    {
                        "id": "gastronomie",
                        "title": "Gastronomie",
                        "icon": "fa-utensils",
                        "content": "<p>Capitale mondiale de la gastronomie. Les bouchons lyonnais sont des institutions. À goûter : quenelles, saucisson brioché, praline rose.</p>"
                    }
                ]
            },
            {
                "slug": "amsterdam",
                "name": "Amsterdam",
                "country": "Pays-Bas",
                "country_code": "NL",
                "image": "/assets/guides/amsterdam-cover.webp",
                "hero_image": "/assets/guides/amsterdam-hero.webp",
                "description": "Ville des canaux, musées et vélos. Hub créatif au cœur de l'Europe.",
                "reading_time": 9,
                "featured": False,
                "tags": ["Thalys", "Vélo", "Culture"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "3h20"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Élevé"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Océanique"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Amsterdam Centraal",
                        "icon": "fa-train",
                        "content": "<p>Gare monumentale en plein centre. Thalys depuis Paris, ICE depuis l'Allemagne. Location de vélos disponible à la sortie.</p>"
                    }
                ]
            },
            {
                "slug": "bruxelles",
                "name": "Bruxelles",
                "country": "Belgique",
                "country_code": "BE",
                "image": "/assets/guides/bruxelles-cover.webp",
                "hero_image": "/assets/guides/bruxelles-hero.webp",
                "description": "Capitale de l'Europe. Gaufres, bandes dessinées et Grand-Place.",
                "reading_time": 8,
                "featured": False,
                "tags": ["Eurostar", "Thalys", "Culture"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "1h22"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Modéré"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Océanique"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Bruxelles-Midi",
                        "icon": "fa-train",
                        "content": "<p>Gare internationale. Eurostar, Thalys et ICE. Connexion rapide vers le centre via métro.</p>"
                    }
                ]
            },
            {
                "slug": "milan",
                "name": "Milan",
                "country": "Italie",
                "country_code": "IT",
                "image": "/assets/guides/milan-cover.webp",
                "hero_image": "/assets/guides/milan-hero.webp",
                "description": "Capitale du design et de la mode. Duomo, Navigli et risotto alla milanese.",
                "reading_time": 10,
                "featured": False,
                "tags": ["Frecciarossa", "Design", "Mode"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "7h"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Élevé"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Continental"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Milano Centrale",
                        "icon": "fa-train",
                        "content": "<p>Gare monumentale de style Art déco. Hub Frecciarossa vers Rome, Florence et Venise.</p>"
                    }
                ]
            },
            {
                "slug": "berlin",
                "name": "Berlin",
                "country": "Allemagne",
                "country_code": "DE",
                "image": "/assets/guides/berlin-cover.webp",
                "hero_image": "/assets/guides/berlin-hero.webp",
                "description": "Capitale alternative et créative. Histoire, techno et currywurst.",
                "reading_time": 12,
                "featured": False,
                "tags": ["ICE", "Culture", "Nightlife"],
                "quick_facts": [
                    {"icon": "fa-clock", "label": "Depuis Paris", "value": "8h"},
                    {"icon": "fa-wifi", "label": "WiFi gare", "value": "Gratuit"},
                    {"icon": "fa-euro-sign", "label": "Coût de vie", "value": "Modéré"},
                    {"icon": "fa-sun", "label": "Climat", "value": "Continental"}
                ],
                "sections": [
                    {
                        "id": "gare",
                        "title": "Berlin Hauptbahnhof",
                        "icon": "fa-train",
                        "content": "<p>Gare centrale moderne inaugurée en 2006. ICE vers toute l'Allemagne, connexions européennes.</p>"
                    }
                ]
            }
        ]
    }

    return guides


def main():
    parser = argparse.ArgumentParser(description='Construit guides.bin.gz')
    parser.add_argument('--input', '-i', default='guides.json', help='Fichier JSON source')
    parser.add_argument('--output', '-o', default='guides.bin.gz', help='Fichier binaire de sortie')
    parser.add_argument('--sample', action='store_true', help='Créer un fichier guides.json exemple')
    args = parser.parse_args()

    if args.sample or not Path(args.input).exists():
        print(f"Création de {args.input} avec des guides exemples...")
        guides_data = create_sample_guides()
        with open(args.input, 'w', encoding='utf-8') as f:
            json.dump(guides_data, f, ensure_ascii=False, indent=2)
        print(f"Fichier {args.input} créé avec {len(guides_data['guides'])} guides")
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            guides_data = json.load(f)

    # Enrichir les guides avec les photo_spots
    print("Ajout des photo_spots aux guides...")
    guides_data = add_photo_spots(guides_data)

    # Sauvegarder le fichier enrichi
    with open(args.input, 'w', encoding='utf-8') as f:
        json.dump(guides_data, f, ensure_ascii=False, indent=2)
    print(f"Fichier {args.input} enrichi avec les photo_spots")

    build_guides_bin(guides_data, args.output)


if __name__ == '__main__':
    main()
