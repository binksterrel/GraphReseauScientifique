"""
Temporal Enrichment Script
==========================
Adds birth_year and death_year attributes to graph nodes
using Wikipedia data. Also adds temporal edge weights.
"""

import networkx as nx
import os
import sys
import math

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wikipedia_client import WikipediaClient

def temporal_weight(source_year: int, target_year: int, half_life: int = 50) -> float:
    """
    Compute temporal weight based on time difference.
    Uses exponential decay: closer in time = stronger weight.
    """
    if source_year is None or target_year is None:
        return 1.0  # Default weight if dates unknown
    
    delta = abs(target_year - source_year)
    return math.exp(-delta / half_life)

def enrich_temporal_data(input_file: str, output_file: str):
    """Add temporal data to graph nodes."""
    print(f"📂 Loading graph from: {input_file}")
    
    try:
        G = nx.read_gexf(input_file)
    except Exception as e:
        print(f"❌ Error loading graph: {e}")
        return
    
    wiki = WikipediaClient()
    
    # Find nodes without temporal data
    nodes_to_enrich = []
    for node, data in G.nodes(data=True):
        birth = data.get('birth_year')
        death = data.get('death_year')
        if birth is None and death is None:
            nodes_to_enrich.append(node)
    
    print(f"🕐 Enriching {len(nodes_to_enrich)} nodes with temporal data...")
    
    enriched_count = 0
    errors = 0
    
    for i, node in enumerate(nodes_to_enrich):
        try:
            birth, death = wiki.extract_years(node)
            
            if birth or death:
                if birth:
                    G.nodes[node]['birth_year'] = birth
                if death:
                    G.nodes[node]['death_year'] = death
                enriched_count += 1
                print(f"  [{i+1}/{len(nodes_to_enrich)}] {node}: {birth or '?'} - {death or '?'}")
            else:
                print(f"  [{i+1}/{len(nodes_to_enrich)}] {node}: No dates found")
                
        except Exception as e:
            errors += 1
            print(f"  [{i+1}/{len(nodes_to_enrich)}] {node}: Error - {e}")
        
        # Progress save every 50 nodes
        if (i + 1) % 50 == 0:
            print(f"  💾 Saving progress...")
            nx.write_gexf(G, output_file)
    
    # Add temporal weights to edges
    print("\n⚡ Computing temporal edge weights...")
    weighted_count = 0
    
    for u, v in G.edges():
        u_birth = G.nodes[u].get('birth_year')
        u_death = G.nodes[u].get('death_year')
        v_birth = G.nodes[v].get('birth_year')
        v_death = G.nodes[v].get('death_year')
        
        # Use midpoint of life as reference year
        u_year = None
        v_year = None
        
        if u_birth and u_death:
            u_year = (u_birth + u_death) // 2
        elif u_birth:
            u_year = u_birth + 30  # Assume active at ~30
        elif u_death:
            u_year = u_death - 30
            
        if v_birth and v_death:
            v_year = (v_birth + v_death) // 2
        elif v_birth:
            v_year = v_birth + 30
        elif v_death:
            v_year = v_death - 30
        
        if u_year and v_year:
            weight = temporal_weight(u_year, v_year)
            G[u][v]['temporal_weight'] = weight
            weighted_count += 1
    
    print(f"   Added temporal weights to {weighted_count} edges")
    
    # Final save
    print(f"\n💾 Saving to: {output_file}")
    nx.write_gexf(G, output_file)
    
    print(f"\n✅ Complete!")
    print(f"   Enriched: {enriched_count} nodes")
    print(f"   Errors: {errors}")
    print(f"   Weighted edges: {weighted_count}")

def main():
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    enrich_temporal_data(gexf_path, gexf_path)

if __name__ == "__main__":
    main()
