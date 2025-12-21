#!/usr/bin/env python3
"""
Sauvegarde une version du graphe actuel avec un timestamp.
Usage: python3 save_version.py [nom_optionnel]
"""

import os
import shutil
import sys
import datetime
# Ajouter le dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys

def main():
    # Nom personnalisé ou timestamp
    if len(sys.argv) > 1:
        version_name = sys.argv[1]
        # Remplacer les caractères problématiques
        version_name = version_name.replace('/', '_').replace('\\', '_')
    else:
        version_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Créer le dossier de sauvegarde (structure simplifiée)
    save_dir = f"saves/{version_name}"
    os.makedirs(save_dir, exist_ok=True)
    
    # Fichiers à sauvegarder
    files_to_save = [
        "output/scientist_graph.gexf",
        "output/index.html"
    ]
    
    saved_count = 0
    for file_path in files_to_save:
        if os.path.exists(file_path):
            dest = os.path.join(save_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest)
            saved_count += 1
            print(f"  ✅ Sauvegardé: {file_path} → {dest}")
        else:
            print(f"  ⚠️  Fichier introuvable: {file_path}")
    
    if saved_count > 0:
        print(f"\n💾 Version '{version_name}' sauvegardée dans: {save_dir}")
        print(f"   {saved_count} fichier(s) sauvegardé(s)")
    else:
        print("❌ Aucun fichier à sauvegarder")

if __name__ == "__main__":
    main()
