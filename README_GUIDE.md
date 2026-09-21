# 🚆 TrainNomad Guides - Manuel Simple

## 3️⃣ Étapes pour ajouter une ville

### **1️⃣ CRÉER LE FICHIER JSON**

Crée un fichier dans le dossier du pays :
```
resultats_guides/France/nice.json
```

Copie ce contenu (template minimal) :

```json
{
  "slug": "nice",
  "name": "Nice",
  "country": "France",
  "country_code": "FR",
  "description": "Perle de la Côte d'Azur. Promenade des Anglais et vieille ville.",
  "reading_time": 10,
  "featured": false,
  "image": "/assets/guides/nice-cover.webp",
  "hero_image": "/assets/guides/nice-hero.webp",
  "tags": ["TGV", "Plage"],
  "quick_facts": [],
  "introduction": "Nice est une belle ville...",
  "essentials": {"to_see": [], "experiences": [], "mobility": []},
  "itinerary": [],
  "practical": [],
  "photo_spots": [
    {
      "name": "Promenade des Anglais",
      "description": "Célèbre promenade",
      "type": "beach",
      "km_from_paris": 910,
      "lat": 43.6640,
      "lon": 7.2263,
      "best_side": "sunset"
    },
    {
      "name": "Colline du Château",
      "description": "Vue panoramique",
      "type": "viewpoint",
      "km_from_paris": 910,
      "lat": 43.6955,
      "lon": 7.2610,
      "best_side": "morning"
    },
    {
      "name": "Vieux Nice",
      "description": "Centre historique",
      "type": "urban",
      "km_from_paris": 910,
      "lat": 43.6978,
      "lon": 7.2735,
      "best_side": "afternoon"
    }
  ]
}
```

---

### **2️⃣ COMPILER (une seule commande)**

```bash
cd C:\Users\PC\Desktop\TrainNomad V2\Backend\guide
bash deploy.sh
```

**Ça compile tout automatiquement :**
- ✅ Scanne les fichiers JSON
- ✅ Génère `index.json`
- ✅ Recompile `guides.bin.gz`
- ✅ Prépare Git

---

### **3️⃣ PUSH SUR GITHUB**

```bash
git commit -m "Guides: add Nice"
git push origin main
```

**Render redéploie automatiquement !** 
Attends 1-2 minutes... puis `Ctrl+F5` sur le site.

---

## 🎯 C'EST TOUT !

Voilà, Nice apparaît sur le site ! 

**Résumé en 3 lignes :**
1. Crée `resultats_guides/France/nice.json`
2. Lance `bash deploy.sh`
3. Fais `git commit -m "..." && git push origin main`

Fini ! 🚀
