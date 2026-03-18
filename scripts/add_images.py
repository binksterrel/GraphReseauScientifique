import networkx as nx
import sys
from wikipedia_client import WikipediaClient
from logger import get_logger

logger = get_logger(__name__)

def add_images_to_graph(gexf_path: str):
    logger.info(f"Loading graph from {gexf_path}")
    graph = nx.read_gexf(gexf_path)
    client = WikipediaClient()
    
    nodes_updated = 0
    total_nodes = len(graph.nodes)
    
    print(f"Adding images to {total_nodes} nodes (might take a minute due to API calls...)")
    for i, node in enumerate(graph.nodes):
        if i % 50 == 0:
            print(f"Progress: {i}/{total_nodes} nodes processed")
            
        if 'image_url' not in graph.nodes[node] or not graph.nodes[node]['image_url']:
            url = client.get_image_url(node)
            if url:
                graph.nodes[node]['image_url'] = url
                nodes_updated += 1
                
    if nodes_updated > 0:
        logger.info(f"Updated {nodes_updated} nodes. Saving to {gexf_path}")
        nx.write_gexf(graph, gexf_path)
    else:
        logger.info("No nodes needed updating.")
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        add_images_to_graph(sys.argv[1])
    else:
        add_images_to_graph("output/scientist_graph_merged.gexf")
