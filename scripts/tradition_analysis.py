"""
Tradition Comparison Analysis
=============================
Compares different scientific traditions (geographic/historical)
by extracting sub-graphs and computing comparative metrics.
"""

import networkx as nx
import os
import sys
from collections import defaultdict

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Geographic/tradition classification based on name patterns and known figures
# This is a simplified heuristic; more accurate classification would use external data
TRADITION_KEYWORDS = {
    "Ancient Greek": [
        "Aristotle", "Plato", "Pythagoras", "Euclid", "Archimedes", "Ptolemy",
        "Hippocrates", "Galen", "Thales", "Democritus", "Heraclitus", "Eudoxus",
        "Apollonius", "Diophantus", "Pappus", "Hypatia", "Eratosthenes"
    ],
    "Islamic Golden Age": [
        "al-Khwarizmi", "Ibn Sina", "Ibn Rushd", "al-Biruni", "Omar Khayyam",
        "al-Razi", "Nasir al-Din", "Ibn al-Haytham", "Jabir", "al-Farabi", "Averroes"
    ],
    "Renaissance Italy": [
        "Galileo", "Leonardo", "Fibonacci", "Cardano", "Tartaglia", "Torricelli",
        "Cavalieri", "Viviani", "Borelli", "Malpighi"
    ],
    "French Enlightenment": [
        "Descartes", "Pascal", "Fermat", "Lagrange", "Laplace", "Lavoisier",
        "d'Alembert", "Condorcet", "Maupertuis", "Clairaut", "Legendre", "Fourier",
        "Poisson", "Cauchy", "Poincaré"
    ],
    "German School": [
        "Leibniz", "Euler", "Gauss", "Riemann", "Weierstrass", "Hilbert", "Klein",
        "Cantor", "Dedekind", "Noether", "Planck", "Heisenberg", "Born", "Sommerfeld"
    ],
    "British Empiricism": [
        "Newton", "Boyle", "Hooke", "Faraday", "Maxwell", "Darwin", "Dalton",
        "Thomson", "Rutherford", "Dirac", "Hawking", "Turing"
    ],
}

def classify_tradition(node_name: str) -> str:
    """Classify a scientist into a tradition based on name matching."""
    node_lower = node_name.lower()
    
    for tradition, keywords in TRADITION_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in node_lower:
                return tradition
    
    return "Other/Modern"

def load_graph(gexf_path: str) -> nx.Graph:
    """Load the graph from GEXF file."""
    print(f"📂 Loading graph from: {gexf_path}")
    g = nx.read_gexf(gexf_path)
    print(f"   {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    return g

def analyze_tradition(G: nx.Graph, nodes: list, tradition_name: str) -> dict:
    """Compute metrics for a tradition's sub-graph."""
    if len(nodes) < 2:
        return None
    
    subgraph = G.subgraph(nodes)
    
    # Basic metrics
    n_nodes = subgraph.number_of_nodes()
    n_edges = subgraph.number_of_edges()
    
    # Density
    density = nx.density(subgraph)
    
    # Clustering (for undirected view)
    try:
        clustering = nx.average_clustering(subgraph.to_undirected())
    except:
        clustering = 0
    
    # Top figure by PageRank
    try:
        pr = nx.pagerank(subgraph)
        top_figure = max(pr, key=pr.get)
        top_pr = pr[top_figure]
    except:
        top_figure = nodes[0] if nodes else "N/A"
        top_pr = 0
    
    # Degree statistics
    degrees = [d for n, d in subgraph.degree()]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    
    return {
        "name": tradition_name,
        "nodes": n_nodes,
        "edges": n_edges,
        "density": density,
        "clustering": clustering,
        "avg_degree": avg_degree,
        "top_figure": top_figure,
        "top_pagerank": top_pr,
    }

def main():
    # Default path
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    G = load_graph(gexf_path)
    
    # Classify all nodes into traditions
    tradition_nodes = defaultdict(list)
    for node in G.nodes():
        tradition = classify_tradition(node)
        tradition_nodes[tradition].append(node)
    
    print("\n📊 COMPARAISON DES TRADITIONS SCIENTIFIQUES")
    print("=" * 80)
    
    # Analyze each tradition
    results = []
    for tradition, nodes in tradition_nodes.items():
        if len(nodes) >= 2:  # Need at least 2 nodes for meaningful analysis
            metrics = analyze_tradition(G, nodes, tradition)
            if metrics:
                results.append(metrics)
    
    # Sort by node count
    results.sort(key=lambda x: x["nodes"], reverse=True)
    
    # Print results
    for r in results:
        print(f"\n🏛️  {r['name']}")
        print(f"    Scientifiques: {r['nodes']}")
        print(f"    Liens internes: {r['edges']}")
        print(f"    Densité du réseau: {r['density']:.4f}")
        print(f"    Coefficient de clustering: {r['clustering']:.4f}")
        print(f"    Connexions moyennes: {r['avg_degree']:.2f}")
        print(f"    Figure dominante: {r['top_figure']} (PR: {r['top_pagerank']:.4f})")
    
    print("\n" + "=" * 80)
    print("💡 Interprétation:")
    print("   - Haute densité = École de pensée très interconnectée")
    print("   - Haut clustering = Cercles intellectuels resserrés")
    print("   - Figure dominante = Personnage le plus influent de cette tradition")
    print("\n   Note: La classification est basée sur les noms et peut être imprécise.")
    print("   Pour de meilleurs résultats, utilisez des bases de données externes.")

if __name__ == "__main__":
    main()
