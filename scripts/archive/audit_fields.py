import networkx as nx
from collections import Counter

def audit_fields(filename="output/scientist_graph.gexf"):
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    total = graph.number_of_nodes()
    missing = 0
    fields = []
    
    for n, data in graph.nodes(data=True):
        field = data.get('field', '').strip()
        if not field or field.lower() in ['unknown', 'none', 'n/a', 'inconnu']:
            missing += 1
        else:
            fields.append(field)
            
    print(f"📊 Audit des Domaines (Fields):")
    print(f"   - Total Nœuds: {total}")
    print(f"   - Manquants: {missing} ({missing/total:.1%})")
    print(f"   - Remplis: {total - missing}")
    
    print("\nTop 10 Domaines existants:")
    for f, count in Counter(fields).most_common(10):
        print(f"   - {f}: {count}")

if __name__ == "__main__":
    audit_fields()
