import networkx as nx
import os
import sys

def remove_isolated(input_file, output_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    initial_count = len(g.nodes())
    print(f"Initial node count: {initial_count}")
    
    # Identify isolated nodes
    isolated = [n for n in g.nodes() if g.degree(n) == 0]
    
    if not isolated:
        print("No isolated nodes found.")
        return

    print(f"Found {len(isolated)} isolated nodes.")
    for node in isolated:
        print(f"Removing isolated node: {node}")
        g.remove_node(node)
        
    final_count = len(g.nodes())
    print(f"Final node count: {final_count}")
    print(f"Removed {len(isolated)} nodes.")
    
    print(f"Saving to {output_file}...")
    nx.write_gexf(g, output_file)
    print("Done.")

if __name__ == "__main__":
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    remove_isolated(gexf_path, gexf_path)
