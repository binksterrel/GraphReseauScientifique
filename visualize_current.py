import networkx as nx
from visualizer import GraphVisualizer
import os

def visualize_only(filename="output/scientist_graph.gexf", output_html="output/graph.html"):
    print(f"🎨 Génération de la visualisation pour: {filename}")
    
    if not os.path.exists(filename):
        print(f"❌ Fichier graphe introuvable: {filename}")
        return

    # Load graph
    try:
        graph = nx.read_gexf(filename)
        print(f"✅ Graphe chargé: {len(graph.nodes())} nœuds, {len(graph.edges())} arêtes.")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du graphe: {e}")
        return

    # Visualize
    try:
        viz = GraphVisualizer(graph)
        viz.create_interactive_html(output_html)
        print(f"✅ Visualisation sauvegardée dans: {output_html}")
    except Exception as e:
        print(f"❌ Erreur lors de la visualisation: {e}")

if __name__ == "__main__":
    visualize_only()
