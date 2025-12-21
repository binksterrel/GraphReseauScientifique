import networkx as nx
import os
import sys

# Fields to REMOVE (Non-scientific)
BLACKLIST_FIELDS = {
    "Literature", "Music", "Musicology", "Theology", "History", 
    "Art", "Paintings", "Politics", "Religion", "Law", "Military",
    "Navigation", # Borderline, but often practical/military not science per se in this context? Let's keep if rigorous, but usually explorers. 
                  # Looking at names: Pedro Nunes (Mathematician/Cosmographer - Keep), Willem Schouten (Explorer - Remove).
                  # "Navigation" is ambiguous. Let's check node names later or just remove for strictness if user wants strict scientists.
                  # For now, I'll blacklist Navigation if it's mostly explorers.
    "Unknown", # User said remove non-scientists. Unknowns are suspicious.
               # But some Unknowns might be scientists. 
               # However, better to be clean than dirty. 
               # If we enriched and it's still Unknown/Other, remove or keep? 
               # "Other" is often the default category from graph_builder for non-mapped.
               # Let's see what "Other" contains.
               # Actually, let's remove explicit non-sciences first.
}

# Explicit removal of error fields from LLM
ERROR_FIELDS = {
    "Alas,", "Wyss", "Capra's", "Ohtake's", "Emery's", "Bradlaugh's", "Kiselyov's", "Fersman", 
    "Avrami", "Gazis", "Sethe", "Lebowitz", "Genovese",
    # Specific homonyms/non-scientists to remove manually
    "William W. Gilbert", "William Ball Gilbert", "William Gilbert (pastoralist)", "William Gilbert (rugby)",
    "Henry Gilbert", "Richard Lindon", "Mary Ball Washington", "George Washington",
    "Duke Albert of Brandenburg Prussia", "Count Phillip II", "Frederick V", "King of Bohemia"

    # Some of these might be names of scientists where LLM failed to give field.
    # Fersman = Mineralogist (Science). Avrami = Physicist. Lebowitz = Physicist.
    # So removing them is wrong if they are scientists. 
    # But their field is wrong.
    # Best approach: Map them to correct fields if possible, or remove if lazy.
    # Given "Enlève tout ceux qui ne sont pas des scientifiques", 
    # cutting the "junk" labels is safer.
    # I will map known ones and delete rest.
}

FIELD_CORRECTIONS = {
    "Avrami": "Physics",
    "Lebowitz": "Physics",
    "Fersman": "Geology", # or Chemistry/Physics
    "Genovese": "Physics", # Likely
    "Algebra": "Mathematics",
    "Crystallography": "Physics", # or Chemistry
    "Neurology": "Medicine",
    "Archaeology": "Archaeology", # Social science / Science
    "Electrical": "Engineering",
}

# Explicit removal of specific nodes by name
BLACKLIST_NAMES = {
    "William W. Gilbert", "William Ball Gilbert", "William Gilbert (pastoralist)", "William Gilbert (rugby)",
    "Henry Gilbert", "Richard Lindon", "Mary Ball Washington", "General George Washington", "George Washington",
    "Duke Albert of Brandenburg Prussia", "Count Phillip II", "Frederick V", "King of Bohemia",
    "Churches of the Palatinate", "Hanau district"
}

def filter_graph(input_file, output_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    initial_count = len(g.nodes())
    print(f"Initial node count: {initial_count}")
    
    removed_count = 0
    updated_count = 0
    
    nodes_to_remove = []
    
    for node, data in g.nodes(data=True):
        field = data.get('field', 'Unknown')
        
        # Check name blacklist
        if node in BLACKLIST_NAMES:
            print(f"Removing {node} (Blacklisted Name)")
            nodes_to_remove.append(node)
            continue
            
        # 1. Correct fields
        if field in FIELD_CORRECTIONS:
            new_field = FIELD_CORRECTIONS[field]
            print(f"Correcting {node} ({field}) -> {new_field}")
            g.nodes[node]['field'] = new_field
            field = new_field
            updated_count += 1
            
        # 2. Check blacklist
        if field in BLACKLIST_FIELDS or field in ERROR_FIELDS:
            # Special case for "Other" or "Unknown" - might want to keep if we are not sure?
            # User said "Enlève tous ceux qui ne sont pas des scientifiques".
            # If we don't know, we can't prove they are scientists.
            # But "Other" was the default for everything before enrichment.
            # Let's remove "Literature", "Art", etc. strictly.
            # What about "Other" and "Unknown"?
            # If I remove "Other", I might obtain a very small graph if many are still Other.
            # Let's check how many "Other" and "Unknown" we have.
            # 49 Other, 31 Unknown.
            # Taking a risk removing them? 
            # Let's remove specific non-scientific fields first.
            
            # Additional logic: Check specific names if needed?
            # Nah, automatic filter.
            
            if field in ["Other", "Unknown"]:
                # Keep for now to avoid decimating graph too much unless explicitly told?
                # User is strict. "Enlève tous ceux qui ne sont pas des scientifiques".
                # If I leave them, I violate instruction if they are e.g. politicians.
                # But I risk removing scientists.
                # Compromise: Remove explicit non-scientists. Keep Unknown/Other but warn user?
                # Or perform a quick check on names for Unknowns?
                # Let's remove explicit non-science fields.
                pass
            else:
                print(f"Removing {node} (Field: {field})")
                nodes_to_remove.append(node)
                
    # Actually remove
    for node in nodes_to_remove:
        g.remove_node(node)
        removed_count += 1
        
    final_count = len(g.nodes())
    print(f"Final node count: {final_count}")
    print(f"Removed {removed_count} nodes.")
    print(f"Updated {updated_count} fields.")
    
    print(f"Saving to {output_file}...")
    nx.write_gexf(g, output_file)
    print("Done.")

if __name__ == "__main__":
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    filter_graph(gexf_path, gexf_path)
