#!/bin/bash
# Deploy tout d'un coup : compile + build binary + ready to push

set -e

echo "=================================================="
echo "1. Compilation des guides (scan resultats_guides/)"
echo "=================================================="
python3 build_guides.py -d resultats_guides

echo ""
echo "=================================================="
echo "2. Recompilation du binaire guides.bin.gz"
echo "=================================================="
python3 << 'EOF'
import json
import struct
import gzip
from datetime import datetime
from pathlib import Path

def write_section(sections, name, dtype, data):
    name_bytes = name.encode('utf-8')[:24].ljust(24, b'\x00')
    count = len(data) if dtype == 1 else len(data) // (1 << (dtype - 1))
    header = name_bytes + struct.pack('<B', dtype) + b'\x00' * 7 + struct.pack('<QQ', count, len(data))
    padding = (8 - len(data) % 8) % 8
    sections.append(header + data + b'\x00' * padding)

guides_dir = 'resultats_guides'
output_path = 'guides.bin.gz'

# Charger index
index_path = Path(guides_dir) / "index.json"
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Charger tous les guides
guides = []
for guide_meta in index['guides']:
    guide_file = Path(guides_dir) / guide_meta['path']
    with open(guide_file, 'r', encoding='utf-8') as f:
        guide = json.load(f)
    guides.append(guide)

# Créer structure binaire
meta = {
    "version": 1,
    "built_at": datetime.now().isoformat(),
    "num_guides": len(guides)
}

sections = []
meta_json = json.dumps(meta, ensure_ascii=False).encode('utf-8')
write_section(sections, "meta", 1, meta_json)

guides_json = json.dumps(guides, ensure_ascii=False).encode('utf-8')
write_section(sections, "guides", 1, guides_json)

header = b"TNGDE001" + struct.pack('<I', len(sections)) + b'\x00' * 4
content = header + b''.join(sections)

with gzip.open(output_path, 'wb') as f:
    f.write(content)

print(f"[OK] {output_path} compile avec {len(guides)} guides")
EOF

echo ""
echo "=================================================="
echo "3. Git - ajout des fichiers"
echo "=================================================="
git add guides.bin.gz resultats_guides/ build_guides.py data.go main.go
echo "[OK] Fichiers stagés"

echo ""
echo "=================================================="
echo "4. Pret pour: git commit + git push"
echo "=================================================="
echo "Commandes a faire :"
echo "  git commit -m 'Guides: recompile all with resultats_guides/'"
echo "  git push origin main"
echo ""
echo "[DONE] Everything compiled and ready!"
