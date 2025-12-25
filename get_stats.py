import networkx as nx

def get_stats(filename="output/scientist_graph.gexf"):
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    nodes = graph.number_of_nodes()
    edges = graph.number_of_edges()
    
    years = []
    for n, data in graph.nodes(data=True):
        y = data.get('birth_year')
        if y:
            try:
                years.append(int(y))
            except:
                pass
                
    min_year = min(years) if years else "N/A"
    max_year = max(years) if years else "N/A"
    
    print(f"NODES={nodes}")
    print(f"EDGES={edges}")
    print(f"MIN_YEAR={min_year}")
    print(f"MAX_YEAR={max_year}")

if __name__ == "__main__":
    get_stats()
