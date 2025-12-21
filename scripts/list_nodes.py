import networkx as nx
import sys
import os

# Add parent directory to path to allow importing from config/parent modules if needed in future
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def list_nodes(filename):
    try:
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return

        graph = nx.read_gexf(filename)
        nodes = sorted(list(graph.nodes()))
        print(f"Total nodes: {len(nodes)}")
        print("-" * 20)
        for node in nodes:
            print(node)
    except Exception as e:
        print(f"Error reading graph: {e}")

if __name__ == "__main__":
    # Point to the correct output directory relative to the script
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    list_nodes(gexf_path)
