import networkx as nx
from visualizer import GraphVisualizer
import os
import json

def load_firecrawl_graph(json_path):
    if not os.path.exists(json_path):
        print(f"⚠️ Graphe Firecrawl introuvable: {json_path}")
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        G = nx.DiGraph()
        for scientist in data.get('scientists', []):
            name = scientist.get('name')
            if not name: continue
            
            G.add_node(name)
            
            for citation in scientist.get('inspired_by', []):
                inspired_name = citation.get('value')
                if inspired_name:
                    G.add_edge(name, inspired_name)
        
        print(f"🔥 Graphe Firecrawl chargé: {len(G.nodes())} nœuds.")
        return G
    except Exception as e:
        print(f"⚠️ Erreur chargement Firecrawl: {e}")
        return None

def visualize_only(filename="output/scientist_graph_merged.gexf", output_html="output/graph.html"):
    print(f"🎨 Génération de la visualisation pour: {filename}")
    
    if not os.path.exists(filename):
        print(f"❌ Fichier graphe introuvable: {filename}")
        return

    # Load graphs
    try:
        graph = nx.read_gexf(filename)
        print(f"✅ Graphe FUSIONNÉ chargé: {len(graph.nodes())} nœuds.")
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement du graphe: {e}")
        return

    # Visualize
    try:
        viz = GraphVisualizer(graph)
        # On ne passe plus d'alt_graph car tout est fusionné
        viz.create_interactive_html(output_html)
        print(f"✅ Visualisation sauvegardée dans: {output_html}")
    except Exception as e:
        print(f"❌ Erreur lors de la visualisation: {e}")
    
if __name__ == "__main__":
    # Par défaut, on filtre un peu pour voir l'effet (ex: Top 150) ou aucun limit pour tout voir nettoyé
    visualize_only()
