import networkx as nx
import json
import os

def merge_graphs():
    base_file = "output/scientist_graph.gexf"
    firecrawl_file = "output/graph_firecrawl.json"
    output_file = "output/scientist_graph_merged.gexf"

    print("🔄 Chargement du graphe principal...")
    G = nx.read_gexf(base_file)
    initial_nodes = len(G.nodes())
    initial_edges = len(G.edges())
    print(f"   ✅ Base : {initial_nodes} nœuds, {initial_edges} arêtes.")

    print("🔄 Chargement des données Firecrawl...")
    with open(firecrawl_file, 'r', encoding='utf-8') as f:
        fc_data = json.load(f)

    # Préparation d'un set de noms normalisés pour la détection
    # On suppose que le graphe principal a des noms propres (Title Case)
    # On va utiliser une map {nom_lower: nom_reel} pour éviter les doublons de casse
    existing_nodes_map = {n.lower(): n for n in G.nodes()}

    added_nodes_count = 0
    added_edges_count = 0

    print("🧩 Fusion en cours...")
    
    for scientist in fc_data.get('scientists', []):
        name = scientist.get('name')
        if not name: continue
        
        name_clean = name.strip()
        name_lower = name_clean.lower()
        
        # 1. Gestion des NŒUDS
        if name_lower in existing_nodes_map:
            # Le nœud existe déjà, on utilise le nom canonique du graphe principal
            canonical_name = existing_nodes_map[name_lower]
        else:
            # Nouveau nœud !
            canonical_name = name_clean
            # On l'ajoute avec un attribut spécifique pour le distinguer
            G.add_node(canonical_name, field="Unknown", source="firecrawl")
            existing_nodes_map[name_lower] = canonical_name # Mise à jour de la map
            added_nodes_count += 1

        # 2. Gestion des ARÊTES
        for citation in scientist.get('inspired_by', []):
            target = citation.get('value')
            if not target: continue
            
            target_clean = target.strip()
            target_lower = target_clean.lower()
            
            # Vérifier si la cible existe
            if target_lower in existing_nodes_map:
                target_canonical = existing_nodes_map[target_lower]
            else:
                # La cible est un nouveau nœud aussi (cité par Firecrawl mais pas dans le graph ni dans la liste scientist de FC ?)
                # On l'ajoute
                target_canonical = target_clean
                G.add_node(target_canonical, field="Unknown", source="firecrawl_target")
                existing_nodes_map[target_lower] = target_canonical
                added_nodes_count += 1
            
            # Ajouter l'arête si elle n'existe pas
            if not G.has_edge(canonical_name, target_canonical):
                G.add_edge(canonical_name, target_canonical)
                added_edges_count += 1

    print(f"✅ Fusion terminée !")
    print(f"   ➕ Nouveaux nœuds : {added_nodes_count}")
    print(f"   ➕ Nouvelles arêtes : {added_edges_count}")
    print(f"   📊 Total final : {len(G.nodes())} nœuds, {len(G.edges())} arêtes.")

    # Sauvegarde
    print(f"💾 Sauvegarde dans {output_file}...")
    nx.write_gexf(G, output_file)
    print("✨ Fichier généré avec succès.")

if __name__ == "__main__":
    merge_graphs()
