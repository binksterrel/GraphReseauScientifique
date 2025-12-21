#!/usr/bin/env python3
"""
Restaure une version sauvegardée.
Usage: python3 restore_version.py <nom_version>
Exemple: python3 restore_version.py 20251218_001234
"""

import os
import shutil
import sys
# Ajouter le dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python3 restore_version.py <nom_version>")
        print("\n💡 Astuce: Lancez 'python3 list_versions.py' pour voir les versions disponibles")
        return
    
    version_name = sys.argv[1]
    save_dir = f"saves/{version_name}"
    
    if not os.path.exists(save_dir):
        print(f"❌ Version '{version_name}' introuvable dans saves/")
        print("\n💡 Versions disponibles:")
        os.system("python3 list_versions.py")
        return
    
    # Sauvegarder la version actuelle avant de restaurer
    print("💾 Sauvegarde de la version actuelle avant restauration...")
    os.system("python3 save_version.py backup_avant_restore")
    
    # Restaurer les fichiers
    files = os.listdir(save_dir)
    restored_count = 0
    
    print(f"\n🔄 Restauration de la version '{version_name}'...\n")
    for file_name in files:
        src = os.path.join(save_dir, file_name)
        dest = os.path.join("output", file_name)
        
        if os.path.isfile(src):
            shutil.copy2(src, dest)
            restored_count += 1
            print(f"  ✅ Restauré: {file_name}")
    
    print(f"\n✅ Version '{version_name}' restaurée avec succès!")
    print(f"   {restored_count} fichier(s) restauré(s) dans output/")
    print("\n💡 Votre version précédente a été sauvegardée comme 'backup_avant_restore'")

if __name__ == "__main__":
    main()
