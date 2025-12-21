import networkx as nx
import os
import sys

# Fields to map to "Other"
TO_OTHER = {
    # User specified
    "ComputerScience",
    "Alchemy",
    "Artusi", # Likely error, but map to Other if user wants
    "Sociology",
    "Psychology",
    "Archaeology",
    "Geology",
    "Paleontology",
    "Egyptology",
    "Neuberg's", # Error
    "Architecture",
    "WarfareStrategy",
    "Missions",
    "Missionary",
    "Unknown" # Map Unknown to Other as well? User listed "Unknown (41)".
}

def remap_fields(input_file, output_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    updated_count = 0
    
    for node, data in g.nodes(data=True):
        field = data.get('field', 'Unknown')
        
        if field in TO_OTHER:
            print(f"Remapping {node}: {field} -> Other")
            g.nodes[node]['field'] = "Other"
            updated_count += 1
            
    print(f"Updated {updated_count} nodes to 'Other'.")
    
    print(f"Saving to {output_file}...")
    nx.write_gexf(g, output_file)
    print("Done.")

if __name__ == "__main__":
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    remap_fields(gexf_path, gexf_path)
