import networkx as nx
from wikipedia_client import WikipediaClient
import re
import time
from llm_extractor import LLMExtractor

def clean_and_repair(filename="output/scientist_graph.gexf"):
    print(f"🧹 Démarrage du nettoyage et réparation sur: {filename}")
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    initial_nodes = graph.number_of_nodes()
    client = WikipediaClient()
    
    # --- STEP 1: REMOVE CONCEPTS & GROUPS ---
    keywords = [
        "theory", "theorem", "law", "principle", "effect", "constant", "equation", "paradox",
        "university", "institute", "department", "society", "association", "club", "group", "school",
        "medal", "prize", "award",
        "journal", "language", "book", "publication", "project", "mission", "program",
        "members", "followers", "residents", "list of", "history of",
        "nobel", "royal", "academy", "people", "scientists", "developers",
        "firstname", "lastname", "professor", "doctor", "dr.", "sir", "lord", "lady",
        "unnamed", "unknown", "students", "researchers", "successors", "colleagues",
        "many", "several", "various", "family", "children", "grandchildren", "wife", "daughter", "son",
        "shoemaker", "captain", "author", "editor", "writer", "novelist", "poet"
    ]
    
    nodes_to_remove = []
    
    for node in list(graph.nodes()):
        lower_name = node.lower()
        
        # Keyword Check
        for kw in keywords:
             if re.search(r'\b' + re.escape(kw) + r'\b', lower_name):
                 print(f"  🗑️ Suppression (Mot-clé '{kw}'): {node}")
                 nodes_to_remove.append(node)
                 break
        
        # Length Check (heuristic: nom trop long = description)
        if len(node) > 40:
             if node not in nodes_to_remove:
                 print(f"  🗑️ Suppression (Nom trop long > 40): {node}")
                 nodes_to_remove.append(node)

    for n in nodes_to_remove:
        graph.remove_node(n)
        
    print(f"✅ Étape 1 terminée: {len(nodes_to_remove)} nœuds supprimés.")
    
    # --- STEP 2: REPAIR MISSING DATA ---
    print("\n🔧 Étape 2: Réparation des données manquantes (Année naissance = 0)...")
    repaired_count = 0
    
    nodes_to_repair = [n for n, d in graph.nodes(data=True) if int(d.get('birth_year', 0)) == 0]
    print(f"   {len(nodes_to_repair)} candidats à réparer.")
    
    try:
        for i, node in enumerate(nodes_to_repair):
            print(f"   [{i+1}/{len(nodes_to_repair)}] Réparation de: {node}")
            try:
                birth_year, _ = client.extract_years(node)
                if birth_year:
                    graph.nodes[node]['birth_year'] = int(birth_year)
                    print(f"     ✅ Trouvé: {birth_year}")
                    repaired_count += 1
                else:
                    print("     ❌ Pas trouvé.")
            except Exception as e:
                print(f"     ⚠️ Erreur: {e}")
            
            # Rate limit
            if i % 10 == 0:
                 time.sleep(0.5)

            # Autosave periodically
            if i > 0 and i % 50 == 0:
                print(f"   💾 Autosave ({i}/{len(nodes_to_repair)})...")
                nx.write_gexf(graph, filename)
                
    except KeyboardInterrupt:
        print("\n🛑 Interruption utilisateur. Sauvegarde en cours...")
        nx.write_gexf(graph, filename)
        print("✅ Sauvegardé.")
        return

    print(f"✅ Étape 2 terminée: {repaired_count} nœuds réparés.")

    # --- SAVE ---
    final_nodes = graph.number_of_nodes()
    nx.write_gexf(graph, filename)
    print("\n" + "="*40)
    print(f"🏁 TERMINÉ")
    print(f"Avant: {initial_nodes} -> Après: {final_nodes}")
    print(f"Sauvegardé dans: {filename}")
    print("="*40)

if __name__ == "__main__":
    clean_and_repair()
