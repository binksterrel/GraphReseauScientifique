"""
Paradigm Shifter Detection (Structural Hole Analysis)
======================================================
Identifies scientists who bridge different intellectual communities.
Based on Burt's structural holes theory (1992).

Key metrics:
- Constraint: Low constraint = bridging position
- Betweenness: High betweenness = "gatekeeper" role
- Cross-community influence: Connects nodes from different clusters
"""

import networkx as nx
import os
import sys
from collections import defaultdict

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_graph(gexf_path: str) -> nx.Graph:
    """Load the graph from GEXF file."""
    print(f"📂 Loading graph from: {gexf_path}")
    g = nx.read_gexf(gexf_path)
    print(f"   {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    return g

def compute_constraint(G: nx.Graph) -> dict:
    """
    Compute Burt's constraint for each node.
    Lower constraint = more bridging potential.
    """
    # NetworkX has a constraint function
    constraint = nx.constraint(G)
    return constraint

def compute_community_bridge_score(G: nx.Graph) -> dict:
    """
    Compute a custom score based on how many different communities a node connects.
    Uses Louvain community detection.
    """
    from networkx.algorithms.community import louvain_communities
    
    # Detect communities
    communities = louvain_communities(G.to_undirected(), resolution=1.0)
    
    # Map node -> community
    node_to_community = {}
    for i, community in enumerate(communities):
        for node in community:
            node_to_community[node] = i
    
    # For each node, count unique communities it connects to
    bridge_scores = {}
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        connected_communities = set()
        for neighbor in neighbors:
            if neighbor in node_to_community:
                connected_communities.add(node_to_community[neighbor])
        
        # Score = number of different communities connected
        bridge_scores[node] = len(connected_communities)
    
    return bridge_scores, node_to_community, communities

def find_paradigm_shifters(G: nx.Graph, top_n: int = 20) -> list:
    """
    Identify paradigm shifters by combining multiple metrics:
    - Low constraint (structural hole)
    - High betweenness centrality
    - High community bridge score
    """
    print("🔬 Computing metrics...")
    
    # Compute betweenness centrality
    betweenness = nx.betweenness_centrality(G)
    print("   ✓ Betweenness centrality")
    
    # Compute constraint (may fail for disconnected nodes)
    try:
        constraint = compute_constraint(G)
        print("   ✓ Constraint (Burt)")
    except Exception as e:
        print(f"   ⚠️ Constraint calculation failed: {e}")
        constraint = {n: 0.5 for n in G.nodes()}  # Default
    
    # Compute community bridge score
    try:
        bridge_scores, node_to_community, communities = compute_community_bridge_score(G)
        print(f"   ✓ Community detection ({len(communities)} communities)")
    except Exception as e:
        print(f"   ⚠️ Community detection failed: {e}")
        bridge_scores = {n: 1 for n in G.nodes()}
    
    # Normalize scores
    max_betweenness = max(betweenness.values()) if betweenness else 1
    max_bridge = max(bridge_scores.values()) if bridge_scores else 1
    
    # Compute composite score
    # Higher is better for paradigm shifter potential
    composite_scores = {}
    for node in G.nodes():
        # Invert constraint (lower is better -> higher score)
        c = constraint.get(node, 0.5)
        constraint_score = (1 - c) if c is not None else 0.5
        
        # Normalize betweenness
        b_score = betweenness.get(node, 0) / max_betweenness
        
        # Normalize bridge score
        bridge_score = bridge_scores.get(node, 0) / max_bridge
        
        # Weighted composite
        composite = (0.4 * b_score) + (0.3 * constraint_score) + (0.3 * bridge_score)
        composite_scores[node] = {
            "composite": composite,
            "betweenness": betweenness.get(node, 0),
            "constraint": c,
            "bridge_score": bridge_scores.get(node, 0),
            "field": G.nodes[node].get("field", "Unknown")
        }
    
    # Sort by composite score
    sorted_nodes = sorted(composite_scores.items(), key=lambda x: x[1]["composite"], reverse=True)
    
    return sorted_nodes[:top_n]

def main():
    # Default path
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    G = load_graph(gexf_path)
    
    print("\n🏆 TOP 20 DES RÉVOLUTIONNAIRES SCIENTIFIQUES (Analyse des Trous Structurels)")
    print("=" * 70)
    
    shifters = find_paradigm_shifters(G, top_n=20)
    
    for i, (node, metrics) in enumerate(shifters, 1):
        field = metrics["field"]
        betw = metrics["betweenness"]
        constr = metrics["constraint"]
        bridge = metrics["bridge_score"]
        composite = metrics["composite"]
        
        print(f"\n{i:2}. {node}")
        print(f"    Domaine: {field}")
        print(f"    Centralité d'intermédiarité: {betw:.4f}")
        print(f"    Contrainte: {constr:.4f}" if constr else "    Contrainte: N/A")
        print(f"    Communautés connectées: {bridge}")
        print(f"    ➡️  Score composite: {composite:.4f}")
    
    print("\n" + "=" * 70)
    print("💡 Interprétation:")
    print("   - Haute intermédiarité = Connecteur clé dans le réseau")
    print("   - Faible contrainte = Relie des groupes séparés (trou structurel)")
    print("   - Nombreuses communautés = Lie des traditions intellectuelles diverses")
    print("\n   Ces scientifiques représentent probablement des ruptures paradigmatiques")
    print("   ou des innovations interdisciplinaires dans l'histoire des sciences.")

if __name__ == "__main__":
    main()
