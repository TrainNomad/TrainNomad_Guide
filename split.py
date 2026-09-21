import json
from pathlib import Path

def split_guides_by_country(input_file="guides.json", base_output_dir="resultats_guides"):
    # Charger le fichier JSON principal
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_file} est introuvable.")
        return
        
    guides = data.get("guides", [])
    print(f"Trouvé {len(guides)} guides à traiter.")
    
    base_path = Path(base_output_dir)
    
    # Traiter chaque guide
    count = 0
    for guide in guides:
        # Récupérer le pays et le slug (ville)
        country = guide.get("country", "inconnu")
        slug = guide.get("slug", f"ville_inconnue_{count}")
        
        # Nettoyer et formater le nom du dossier pays
        country_folder = country.strip()
        
        # Créer le sous-dossier pour le pays
        country_path = base_path / country_folder
        country_path.mkdir(parents=True, exist_ok=True)
        
        # Enregistrer le fichier JSON de la ville dans le dossier du pays
        file_path = country_path / f"{slug}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(guide, f, ensure_ascii=False, indent=2)
            
        print(f"-> Sauvegardé : {country_folder}/{slug}.json")
        count += 1

    print(f"\nOpération terminée ! {count} fichiers organisés dans le dossier '{base_output_dir}/'.")

if __name__ == "__main__":
    split_guides_by_country()