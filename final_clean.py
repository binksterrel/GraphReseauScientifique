import networkx as nx
import re

def final_clean(filename="output/scientist_graph.gexf"):
    print(f"🧼 Finition du nettoyage sur: {filename}")
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    keywords = [
        "tradition", "novelty", "observatory", "temple", "polytechnique", 
        "university", "universität", "bureau", "office", "commission",
        "laboratory", "laboratoire", "institute", "institut",
        "duc d'", "baron", "abbé", "reverend", "father", "mother",
        "actuary", "mathematician", "physicist", "chemist", "biologist",
        "unnamed", "unknown", "anonymous"
    ]
    
    nodes_to_remove = []
    
    for node in list(graph.nodes()):
        lower_name = node.lower()
        
        # Keyword Check
        for kw in keywords:
             if re.search(r'\b' + re.escape(kw) + r'\b', lower_name):
                 print(f"  🗑️ Suppression Finale (Mot-clé '{kw}'): {node}")
                 nodes_to_remove.append(node)
                 break
                 
    for n in nodes_to_remove:
        graph.remove_node(n)

    nx.write_gexf(graph, filename)
    print(f"✅ Nettoyage final terminé: {len(nodes_to_remove)} nœuds supprimés.")

if __name__ == "__main__":
    final_clean()
