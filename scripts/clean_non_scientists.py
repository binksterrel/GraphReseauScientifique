#!/usr/bin/env python3
"""
Nettoie le graphe en retirant les personnes sans domaine scientifique reconnu.
Usage: python3 clean_non_scientists.py
"""

import sys
import os
# Ajouter le dossier parent au path pour pouvoir importer les modules racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
from visualizer import GraphVisualizer
from config import BLACKLIST

def main():
    gexf_path = "output/scientist_graph.gexf"
    
    print(f"📂 Chargement du graphe: {gexf_path}")
    g = nx.read_gexf(gexf_path)
    original_nodes = g.number_of_nodes()
    original_edges = g.number_of_edges()
    print(f"   {original_nodes} nœuds, {original_edges} arêtes")
    
    # Domaines scientifiques reconnus
    scientific_fields = [
        'Physics', 'Mathematics', 'Chemistry', 'Biology', 
        'Computer Science', 'Medicine', 'Astronomy', 
        'Engineering', 'Philosophy', 'Economics'
    ]
    
    # Identifier les nœuds à supprimer (ceux sans domaine scientifique)
    nodes_to_remove = []
    for node in g.nodes():
        field = g.nodes[node].get('field', None)
        if not field or field == 'Other' or field not in scientific_fields:
            nodes_to_remove.append(node)
    
    print(f"\n🗑️  {len(nodes_to_remove)} nœuds à supprimer (sans domaine scientifique)")
    
    # Quelques exemples de ce qui sera supprimé
    if nodes_to_remove:
        print("   Exemples:", nodes_to_remove[:5])
    
    # Confirmer
    confirm = input("\n❓ Voulez-vous supprimer ces nœuds ? (oui/non): ").strip().lower()
    if confirm != 'oui':
        print("❌ Opération annulée")
        return
    
    # Supprimer
    g.remove_nodes_from(nodes_to_remove)
    
    final_nodes = g.number_of_nodes()
    final_edges = g.number_of_edges()
    
    print(f"\n✅ Nettoyage terminé:")
    print(f"   Nœuds: {original_nodes} → {final_nodes} (-{original_nodes - final_nodes})")
    print(f"   Arêtes: {original_edges} → {final_edges} (-{original_edges - final_edges})")
    
    # Statistiques des domaines restants
    print("\n📊 Répartition des domaines:")
    fields = {}
    for n in g.nodes():
        f = g.nodes[n].get('field', 'Unknown')
        fields[f] = fields.get(f, 0) + 1
    for f, c in sorted(fields.items(), key=lambda x: -x[1]):
        print(f"   {f}: {c}")
    
    # Sauvegarder
    nx.write_gexf(g, gexf_path)
    print(f"\n💾 Graphe nettoyé sauvegardé: {gexf_path}")
    print("   Lancez 'python3 regenerate_viz.py' pour actualiser la visualisation")

if __name__ == "__main__":
    main()
