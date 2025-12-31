import networkx as nx

def audit_graph(filename="output/scientist_graph.gexf"):
    print(f"🕵️‍♂️ Audit RAPIDE du graphe: {filename}")
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    nodes = list(graph.nodes(data=True))
    total = len(nodes)
    
    suspicious = []
    
    print(f"📋 Analyse heuristique de {total} nœuds...")
    
    keywords = [
        "theory", "theorem", "law", "principle", "effect", "constant", "equation", "paradox",
        "university", "institute", "department", "society", "association", "club", "group", "school",
        "medal", "prize", "award",
        "journal", "language", "book", "publication",
        "members", "followers", "residents", "list of", "history of",
        "nobel", "royal", "academy"
    ]
    
    for node_id, data in nodes:
        reason = None
        
        # 1. Check Birth Year (Indicateur très fort)
        # Note: GEXF stores generic attributes, sometimes as strings or ints.
        # graph_builder puts 0 if not found.
        birth_year = data.get('birth_year', 0)
        try:
            birth_year = int(birth_year)
        except:
            birth_year = 0
            
        if birth_year == 0:
            reason = "Année de naissance manquante (0)"
        
        # 2. Check Name Keywords (Concept/Orga)
        if not reason:
            lower_name = node_id.lower()
            for kw in keywords:
                # On vérifie " word " ou " word" ou "word " pour éviter les faux positifs (ex: Law - Lawrence)
                # Mais simplifions : si le mot est dans le nom
                 import re
                 if re.search(r'\b' + re.escape(kw) + r'\b', lower_name):
                     reason = f"Mot-clé suspect: '{kw}'"
                     break

        if reason:
            print(f"  🚩 SUSPECT: [{node_id}] -> {reason}")
            suspicious.append((node_id, reason))
            
    print("\n" + "="*40)
    print(f"🛑 Total Suspects identifiés: {len(suspicious)} / {total}")
    print("="*40)
    # Trier par raison pour grouper
    suspicious.sort(key=lambda x: x[1])
    for s in suspicious:
        print(f" - {s[0]} ({s[1]})")

if __name__ == "__main__":
    audit_graph()
