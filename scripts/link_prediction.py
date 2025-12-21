"""
Link Prediction for Missing Influence Relations
================================================
Uses graph-based similarity metrics to predict potential
influence relationships that may not be documented.

Metrics used:
- Jaccard Coefficient
- Adamic-Adar Index
- Common Neighbors
- Preferential Attachment
"""

import networkx as nx
import os
import sys
from itertools import combinations

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_graph(gexf_path: str) -> nx.Graph:
    """Charge le graphe depuis le fichier GEXF."""
    print(f"📂 Chargement du graphe depuis: {gexf_path}")
    g = nx.read_gexf(gexf_path)
    print(f"   {g.number_of_nodes()} nœuds, {g.number_of_edges()} arêtes")
    return g

def compute_link_predictions(G: nx.Graph, top_n: int = 50) -> list:
    """
    Calcule les scores de prédiction de liens pour les arêtes inexistantes.
    Retourne les top N liens prédits.
    """
    print("🔮 Calcul des prédictions de liens...")
    
    # Convert to undirected for prediction metrics
    G_undirected = G.to_undirected()
    
    # Get all non-edges (pairs without edges)
    nodes = list(G_undirected.nodes())
    existing_edges = set(G_undirected.edges())
    
    # Sample non-edges (too many to compute all)
    print("   Échantillonnage des non-arêtes pour l'analyse...")
    non_edges = []
    for i, u in enumerate(nodes):
        for v in nodes[i+1:]:
            if (u, v) not in existing_edges and (v, u) not in existing_edges:
                non_edges.append((u, v))
                if len(non_edges) >= 10000:  # Limit for performance
                    break
        if len(non_edges) >= 10000:
            break
    
    print(f"   Analyse de {len(non_edges)} liens potentiels...")
    
    # Compute Jaccard coefficient
    jaccard_scores = {}
    for u, v, score in nx.jaccard_coefficient(G_undirected, non_edges):
        jaccard_scores[(u, v)] = score
    print("   ✓ Coefficient de Jaccard")
    
    # Compute Adamic-Adar index
    adamic_adar_scores = {}
    for u, v, score in nx.adamic_adar_index(G_undirected, non_edges):
        adamic_adar_scores[(u, v)] = score
    print("   ✓ Indice d'Adamic-Adar")
    
    # Compute preferential attachment
    pref_attach_scores = {}
    for u, v, score in nx.preferential_attachment(G_undirected, non_edges):
        pref_attach_scores[(u, v)] = score
    print("   ✓ Attachement préférentiel")
    
    # Compute common neighbors count
    common_neighbors_scores = {}
    for u, v in non_edges:
        cn = len(list(nx.common_neighbors(G_undirected, u, v)))
        common_neighbors_scores[(u, v)] = cn
    print("   ✓ Voisins communs")
    
    # Normalize and combine scores
    predictions = []
    for edge in non_edges:
        u, v = edge
        
        # Get individual scores
        jaccard = jaccard_scores.get(edge, 0)
        adamic = adamic_adar_scores.get(edge, 0)
        pref = pref_attach_scores.get(edge, 0)
        common = common_neighbors_scores.get(edge, 0)
        
        # Skip if no common neighbors (unlikely to be connected)
        if common == 0:
            continue
        
        # Normalize preferential attachment (can be very large)
        norm_pref = min(pref / 100, 1.0)
        
        # Composite score (weighted average)
        composite = (0.3 * jaccard) + (0.4 * adamic) + (0.15 * norm_pref) + (0.15 * min(common / 5, 1.0))
        
        predictions.append({
            "source": u,
            "target": v,
            "jaccard": jaccard,
            "adamic_adar": adamic,
            "pref_attach": pref,
            "common_neighbors": common,
            "composite": composite,
            "source_field": G.nodes[u].get("field", "Unknown"),
            "target_field": G.nodes[v].get("field", "Unknown"),
        })
    
    # Sort by composite score
    predictions.sort(key=lambda x: x["composite"], reverse=True)
    
    return predictions[:top_n]

def main():
    # Default path
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    G = load_graph(gexf_path)
    
    print("\n🔮 TOP 30 DES LIENS MANQUANTS PRÉDITS")
    print("=" * 80)
    print("Ces relations d'influence potentielles ne sont pas documentées actuellement")
    print("mais sont statistiquement probables selon la structure du réseau.")
    print("=" * 80)
    
    predictions = compute_link_predictions(G, top_n=30)
    
    for i, pred in enumerate(predictions, 1):
        src = pred["source"]
        tgt = pred["target"]
        src_field = pred["source_field"]
        tgt_field = pred["target_field"]
        common = pred["common_neighbors"]
        composite = pred["composite"]
        
        print(f"\n{i:2}. {src} ↔ {tgt}")
        print(f"    Domaines: {src_field} ↔ {tgt_field}")
        print(f"    Connexions communes: {common}")
        print(f"    Score de prédiction: {composite:.4f}")
    
    print("\n" + "=" * 80)
    print("💡 Utilisation de ces prédictions:")
    print("   1. Rechercher ces paires dans les sources historiques")
    print("   2. Chercher des influences indirectes (professeurs communs, institutions)")
    print("   3. Envisager d'ajouter les liens validés pour améliorer le graphe")

if __name__ == "__main__":
    main()
