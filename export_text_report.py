import networkx as nx

def export_report(filename="output/scientist_graph.gexf", output_txt="output/scientists_report.txt"):
    print(f"📄 Génération du rapport texte depuis: {filename}")
    try:
        graph = nx.read_gexf(filename)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    nodes = sorted(list(graph.nodes(data=True)), key=lambda x: x[0])
    
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write(f"RAPPORT D'INFLUENCE SCIENTIFIQUE\n")
        f.write(f"Nombre de scientifiques: {len(nodes)}\n")
        f.write("="*60 + "\n\n")
        
        for node_id, data in nodes:
            # Influenced By (Predecessors) -> Les gens qui ont influencé ce scientifique
            # Dans le graphe A -> B signifie "A a influencé B"
            # Donc Predecessors de B sont ceux qui l'ont influencé (A)
            
            influenced_by = sorted(list(graph.predecessors(node_id)))
            influenced_others = sorted(list(graph.successors(node_id)))
            
            birth = data.get('birth_year', 'Inconnu')
            field = data.get('field', 'Non spécifié')
            
            f.write(f"🧑‍🔬 {node_id} ({birth}) - {field}\n")
            
            # A été influencé par...
            if influenced_by:
                f.write(f"   ⬅️  A été influencé par ({len(influenced_by)}) :\n")
                for p in influenced_by:
                    f.write(f"       - {p}\n")
            else:
                f.write("   ⬅️  Influencé par : Personne (dans ce graphe)\n")
                
            # A influencé...
            if influenced_others:
                f.write(f"   ➡️  A influencé ({len(influenced_others)}) :\n")
                for s in influenced_others:
                    f.write(f"       - {s}\n")
            else:
                 f.write("   ➡️  A influencé : Personne (dans ce graphe)\n")
            
            f.write("\n" + "-"*40 + "\n\n")

    print(f"✅ Rapport sauvegardé dans: {output_txt}")

if __name__ == "__main__":
    export_report()
