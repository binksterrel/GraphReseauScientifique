import networkx as nx
import os
import sys
from collections import Counter

def check_fields(input_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    fields = []
    missing_count = 0
    
    for node, data in g.nodes(data=True):
        field = data.get('field', 'Unknown')
        if not field or field == 'Unknown':
            missing_count += 1
            fields.append('Unknown')
        else:
            fields.append(field)

    print(f"Total nodes: {len(g.nodes())}")
    print(f"Nodes with 'Unknown' field: {missing_count}")
    print("-" * 20)
    print("Field Distribution:")
    
    counts = Counter(fields)
    for field, count in counts.most_common():
        print(f"{field}: {count}")

if __name__ == "__main__":
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    check_fields(gexf_path)
