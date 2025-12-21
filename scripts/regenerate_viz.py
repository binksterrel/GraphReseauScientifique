#!/usr/bin/env python3
"""
Script pour régénérer la visualisation à partir du graphe sauvegardé.
Usage: python3 regenerate_viz.py
"""

import sys
import os
# Ajouter le dossier parent au path pour pouvoir importer les modules racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
from visualizer import GraphVisualizer

def main():
    gexf_path = "output/scientist_graph.gexf"
    html_path = "output/graph.html"
    
    if not os.path.exists(gexf_path):
        print(f"❌ Fichier introuvable: {gexf_path}")
        print("   Lancez d'abord 'python3 main.py' pour générer le graphe.")
        return
    
    print(f"📂 Chargement du graphe depuis: {gexf_path}")
    g = nx.read_gexf(gexf_path)
    print(f"   {g.number_of_nodes()} nœuds, {g.number_of_edges()} arêtes")
    
    print("🎨 Génération de la visualisation...")
    GraphVisualizer(g).create_interactive_html(html_path)
    
    print(f"\n✅ Visualisation régénérée: {html_path}")
    print("   Ouvrez ce fichier dans votre navigateur.")

if __name__ == "__main__":
    main()
