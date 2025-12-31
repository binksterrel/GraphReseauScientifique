import networkx as nx
import time
from llm_extractor import LLMExtractor
import os

def enrich_fields(input_file="output/scientist_graph.gexf", output_file="output/scientist_graph.gexf"):
    print(f"🔧 Chargement du graphe : {input_file}")
    try:
        graph = nx.read_gexf(input_file)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    llm = LLMExtractor()
    if not llm.check_connection():
        print("❌ Impossible de se connecter au LLM. Abandon.")
        return

    nodes_to_process = []
    for node, data in graph.nodes(data=True):
        field = data.get('field', '').strip()
        if not field or field.lower() in ['unknown', 'none', 'n/a', 'inconnu']:
            nodes_to_process.append(node)
    
    total = len(nodes_to_process)
    print(f"🎯 {total} scientifiques sans domaine identifiés.")
    
    if total == 0:
        print("✅ Tous les champs sont déjà remplis !")
        return

    count = 0
    start_time = time.time()
    
    try:
        for scientist in nodes_to_process:
            count += 1
            print(f"[{count}/{total}] Enrichissement : {scientist}")
            
            field = llm.identify_field(scientist)
            
            # Mise à jour du graphe
            graph.nodes[scientist]['field'] = field
            
            # Autosave toutes les 20 requêtes
            if count % 20 == 0:
                nx.write_gexf(graph, output_file)
                print(f"💾 Sauvegarde intermédiaire ({count} traités)...")
                
                # Petite pause pour éviter le rate limit si API
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n⚠️ Interruption utilisateur. Sauvegarde en cours...")
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
    finally:
        # Sauvegarde finale
        nx.write_gexf(graph, output_file)
        duration = time.time() - start_time
        print(f"\n✅ Terminé ! {count}/{total} champs enrichis en {duration:.1f}s.")
        print(f"💾 Graphe sauvegardé : {output_file}")

if __name__ == "__main__":
    enrich_fields()
