import networkx as nx
import os
import sys

# List of nodes to remove (Groups, Institutions, Concepts, Placeholders)
NODES_TO_REMOVE = [
    # Placeholders / Errors
    "Name not provided in text",
    "Not found in the provided text",
    "Not specified",
    "Unknown",
    "Unknown (Desarguesian plane, non-Desarguesian plane, Desargues' theorem, Desargues graph, Desargues configuration)",
    
    # Concepts / Movements / Ethics
    "Dialectical materialism",
    "Stoic ethics",
    "English and Scottish Enlightenment",
    "Gestalt psychologists",
    "Greek thinkers",
    "Arab thinkers",
    "Islamic scholars during the Golden Age",
    "European scholars starting in the 12th century",
    "Scottish neurologist",
    
    # Institutions / Academies / Societies
    "Bavarian Academy of Sciences and Humanities",
    "Russian Academy of Sciences",
    "Society of Antiquaries of London",
    "South Place Ethical Society",
    "Parnassus Boicus",
    "Hashomer Hatzair",
    "Left Poale Zionist",
    
    # Groups of people
    "Bernoulli family",
    "Grimm brothers",
    "Future students of Friedrich Kohlrausch (physicist)",
    "Students of Theodore William Richards",
    "Scientists who have built upon Fresneau's work on rubber and waterproof materials",
    
    # Fictional / Others
    "The Accountant (character)",
    "The Accountant", 
]

# Additional mappings missed in previous deduplication
ADDITIONAL_MERGES = {
    "Bishop Berkeley": "George Berkeley",
    "Francesco Buonamici (1596–1677)": "Francesco Buonamici", # Assuming the main one is intended
    "Francesco Buonamici (1836–1921)": "Francesco Buonamici", # Merge to simple name or keep distinct? 
                                                              # If simple "Francesco Buonamici" exists, it's ambiguous.
                                                              # Let's check if "Francesco Buonamici" exists. 
                                                              # Based on previous output, "Francesco Buonamici" exists.
                                                              # It's safer to keep dates if we want precision, but for this graph 
                                                              # merging to the most famous one (Galileo's teacher) is likely intended.
                                                              # Let's merge for cleaner visual.
}

def clean_graph(input_file, output_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    initial_count = len(g.nodes())
    print(f"Initial node count: {initial_count}")
    
    removed_count = 0
    
    # 1. Remove specific nodes
    for node in NODES_TO_REMOVE:
        if g.has_node(node):
            print(f"Removing node: {node}")
            g.remove_node(node)
            removed_count += 1
            
    # 2. Perform additional merges
    merged_count = 0
    for variant, canonical in ADDITIONAL_MERGES.items():
        if g.has_node(variant):
            if not g.has_node(canonical):
                print(f"Renaming '{variant}' to '{canonical}'")
                mapping = {variant: canonical}
                g = nx.relabel_nodes(g, mapping, copy=False)
            else:
                print(f"Merging '{variant}' into '{canonical}'")
                for neighbor in g.neighbors(variant):
                    if neighbor == canonical: continue
                    if not g.has_edge(canonical, neighbor):
                        g.add_edge(canonical, neighbor)
                g.remove_node(variant)
                merged_count += 1

    final_count = len(g.nodes())
    print(f"Final node count: {final_count}")
    print(f"Removed {removed_count} invalid nodes.")
    print(f"Merged {merged_count} additional duplicates.")
    
    print(f"Saving to {output_file}...")
    nx.write_gexf(g, output_file)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    else:
        gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    
    clean_graph(gexf_path, gexf_path)
