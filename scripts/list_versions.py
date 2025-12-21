#!/usr/bin/env python3
"""
Liste toutes les versions sauvegardées.
Usage: python3 list_versions.py
"""

import os
import sys
# Ajouter le dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime

def main():
    save_base = "saves"
    
    if not os.path.exists(save_base):
        print("📂 Aucune sauvegarde trouvée.")
        print(f"   Lancez 'python3 save_version.py' pour créer votre première sauvegarde.")
        return
    
    versions = []
    for item in os.listdir(save_base):
        path = os.path.join(save_base, item)
        if os.path.isdir(path):
            # Récupérer le timestamp de modification
            mtime = os.path.getmtime(path)
            versions.append({
                'name': item,
                'path': path,
                'date': datetime.fromtimestamp(mtime)
            })
    
    if not versions:
        print("📂 Aucune version sauvegardée.")
        return
    
    # Trier par date (plus récent en premier)
    versions.sort(key=lambda x: x['date'], reverse=True)
    
    print(f"📚 {len(versions)} version(s) sauvegardée(s) :\n")
    for i, v in enumerate(versions, 1):
        # Compter les fichiers
        files = os.listdir(v['path'])
        date_str = v['date'].strftime("%d/%m/%Y %H:%M:%S")
        print(f"  {i}. {v['name']}")
        print(f"     📅 {date_str} | 📄 {len(files)} fichier(s)")
        print()

if __name__ == "__main__":
    main()
