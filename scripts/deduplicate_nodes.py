import networkx as nx
import os
import sys

# Map of Variant -> Canonical Name
DUPLICATE_MAPPING = {
    # Bose
    "S. N. Bose": "Satyendra Nath Bose",
    "Satyendranath Bose": "Satyendra Nath Bose",
    
    # Pauli
    "Wolfgang Ernst Pauli": "Wolfgang Pauli",
    
    # Leibniz
    "Gottfried Leibniz": "Gottfried Wilhelm Leibniz",
    
    # Spinoza
    "Baruch de Spinoza": "Baruch Spinoza",
    
    # Lalande
    "Jérome Lalande": "Joseph Jérôme Lefrançois de Lalande",
    "Jérôme Lalande": "Joseph Jérôme Lefrançois de Lalande",
    "Joseph Jérôme Lefrançois de Lalande": "Joseph Jérôme Lefrançois de Lalande", # Canonical
    "Michel Lefrançois de Lalande": "Michel Lefrançois de Lalande", # Different person, keep
    
    # Lepaute
    "Nicole Reine Lepaute": "Nicole-Reine Lepaute",
    
    # Sluze
    "René-François de Sluse": "René de Sluze",
    
    # Carnot
    "Nicolas Léonard Sadi Carnot": "Sadi Carnot",
    
    # Darwin
    # "Charles Darwin" is canonical
    
    # William Gilbert
    # There are multiple William Gilberts, we must be careful. 
    # "William Gilbert" (physicist) vs "W. S. Gilbert" (writer) vs "William Ball Gilbert".
    # We will assume "William Gilbert" is the physicist in this context, but leave others if they are distinct.
    
    # Jussieu
    # Antoine, Bernard, Joseph are distinct.
    
    # Buonamici - distinct people with dates, keep them separate if dates are present to distinguish.
    
    # Descartes
    "René Descartes": "René Descartes",
    
    # New additions
    "Franz Simon": "Francis Simon",
    "Sir Robert Mond": "Robert Mond",
    "Chandrasekhara Venkata Raman": "C. V. Raman",
    "Willebrord Snell": "Willebrord Snellius",
    "Snellius": "Willebrord Snellius", # Ambiguous but usually Willebrord
    "Jan Swammerdam": "Jan Swammerdam", # Self
    "Herman Boerhaave": "Hermann Boerhaave",
    "Christian Huygens": "Christiaan Huygens",
    "Christiaan Huyghens": "Christiaan Huygens",
    "Tycho Brahe": "Tycho Brahe", # Canonical
    "Tycho": "Tycho Brahe",
    "Kepler": "Johannes Kepler",
    "Johan Kepler": "Johannes Kepler",
    "Copernicus": "Nicolaus Copernicus",
    "Nicolas Copernicus": "Nicolaus Copernicus",
    "Galileo": "Galileo Galilei",
    "Galilée": "Galileo Galilei",
    "Newton": "Isaac Newton",
    "Sir Isaac Newton": "Isaac Newton",
}

def deduplicate_graph(input_file, output_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    initial_count = len(g.nodes())
    print(f"Initial node count: {initial_count}")
    
    merged_count = 0
    
    for variant, canonical in DUPLICATE_MAPPING.items():
        if variant == canonical:
            continue
            
        if g.has_node(variant):
            # If canonical doesn't exist, just rename
            if not g.has_node(canonical):
                print(f"Renaming '{variant}' to '{canonical}'")
                # nx.relabel_nodes returns a copy or modifies in place depending on copy=False
                # But it's easier to do it step by step for merging
                mapping = {variant: canonical}
                g = nx.relabel_nodes(g, mapping, copy=False)
            else:
                # Both exist, merge variant into canonical
                print(f"Merging '{variant}' into '{canonical}'")
                
                # Move edges
                for neighbor in g.neighbors(variant):
                    # Avoid self-loops if variant connected to canonical
                    if neighbor == canonical:
                        continue
                    
                    # Add edge to canonical if not exists (or update weight?)
                    # For simple graph, just ensure edge exists.
                    if not g.has_edge(canonical, neighbor):
                        g.add_edge(canonical, neighbor)
                
                # Remove variant
                g.remove_node(variant)
                merged_count += 1

    final_count = len(g.nodes())
    print(f"Final node count: {final_count}")
    print(f"Merged {merged_count} duplicates.")
    
    print(f"Saving to {output_file}...")
    nx.write_gexf(g, output_file)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    else:
        # Default path
        gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    
    deduplicate_graph(gexf_path, gexf_path)
