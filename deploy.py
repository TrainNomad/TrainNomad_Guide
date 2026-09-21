#!/usr/bin/env python3
"""
Deploy script - Compile all guides in one command
Works on Windows, Mac, Linux
"""

import json
import struct
import gzip
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def run_build_guides():
    """Run the build_guides.py script"""
    print_section("1. Scanning resultats_guides/")
    result = subprocess.run([sys.executable, "build_guides.py", "-d", "resultats_guides"],
                          capture_output=False)
    if result.returncode != 0:
        print("[ERROR] build_guides.py failed")
        return False
    return True

def compile_binary():
    """Recompile guides.bin.gz from index.json"""
    print_section("2. Recompiling guides.bin.gz")

    def write_section(sections, name, dtype, data):
        name_bytes = name.encode('utf-8')[:24].ljust(24, b'\x00')
        count = len(data) if dtype == 1 else len(data) // (1 << (dtype - 1))
        header = name_bytes + struct.pack('<B', dtype) + b'\x00' * 7 + struct.pack('<QQ', count, len(data))
        padding = (8 - len(data) % 8) % 8
        sections.append(header + data + b'\x00' * padding)

    try:
        guides_dir = 'resultats_guides'
        output_path = 'guides.bin.gz'

        # Load index
        index_path = Path(guides_dir) / "index.json"
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)

        # Load all guides
        guides = []
        for guide_meta in index['guides']:
            guide_file = Path(guides_dir) / guide_meta['path']
            with open(guide_file, 'r', encoding='utf-8') as f:
                guide = json.load(f)
            guides.append(guide)

        # Build binary structure
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

        print(f"[OK] {output_path} compiled with {len(guides)} guides")
        return True

    except Exception as e:
        print(f"[ERROR] Compilation failed: {e}")
        return False

def git_add_files():
    """Stage files for git"""
    print_section("3. Git - Adding files")

    try:
        files = [
            "guides.bin.gz",
            "resultats_guides/",
            "build_guides.py",
            "data.go",
            "main.go",
            "deploy.py"
        ]

        for f in files:
            subprocess.run(["git", "add", f], capture_output=True)

        print("[OK] Files staged for commit")
        return True
    except Exception as e:
        print(f"[ERROR] Git add failed: {e}")
        return False

def main():
    print("\n" + "=" * 50)
    print("TRAINNOMAD GUIDES - DEPLOY")
    print("=" * 50)

    if not run_build_guides():
        sys.exit(1)

    if not compile_binary():
        sys.exit(1)

    if not git_add_files():
        sys.exit(1)

    print_section("4. Ready to commit & push")
    print("\nNext steps:")
    print("  git commit -m 'Guides: update from resultats_guides/'")
    print("  git push origin main")
    print("\n[DONE] Everything compiled and staged!")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
