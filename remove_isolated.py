import networkx as nx

def remove_isolated(filename="output/scientist_graph.gexf"):
    print(f"🕸️ Suppression des nœuds isolés sur: {filename}")
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    initial_count = graph.number_of_nodes()
    
    # Identifier les composantes connexes (Graph Dirigé -> Weakly Connected)
    # On convertit en non-dirigé pour la notion de "groupe"
    if nx.is_directed(graph):
        components = list(nx.weakly_connected_components(graph))
    else:
        components = list(nx.connected_components(graph))
        
    components.sort(key=len, reverse=True)
    
    if not components:
        print("❌ Graphe vide.")
        return

    largest_component = components[0]
    num_components = len(components)
    
    print(f"📊 Analyse des groupes :")
    print(f"   - Nombre de groupes (composantes): {num_components}")
    print(f"   - Taille du plus grand groupe: {len(largest_component)}")
    
    if num_components > 1:
        nodes_to_remove = []
        for comp in components[1:]:
            nodes_to_remove.extend(comp)
            
        graph.remove_nodes_from(nodes_to_remove)
        print(f"✅ Suppression de {num_components - 1} petits groupes isolés.")
        print(f"   (Total {len(nodes_to_remove)} nœuds supprimés)")
    else:
        print("✅ Le graphe est déjà entièrement connecté (1 seul groupe).")
        
    final_count = graph.number_of_nodes()
    
    if initial_count != final_count:
        nx.write_gexf(graph, filename)
        print(f"💾 Graphe sauvegardé ({final_count} nœuds restants).")
        
    print("-" * 30)
    print(f"Avant: {initial_count}")
    print(f"Après: {final_count}")
    print("-" * 30)

if __name__ == "__main__":
    remove_isolated()
