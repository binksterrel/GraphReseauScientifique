import networkx as nx
import re
import collections

def post_process_graph(input_file="output/scientist_graph.gexf", output_file="output/scientist_graph_clean.gexf"):
    print(f"🔧 Démarrage du Post-Processing V4 (Ultra-Clean) sur: {input_file}")
    try:
        graph = nx.read_gexf(input_file)
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    initial_nodes = graph.number_of_nodes()
    
    # ==========================================
    # 1. FILTRAGE "TRASH" (Garbage Collection)
    # ==========================================
    # Liste enrichie selon retours utilisateur
    garbage_keywords = [
        "neurosu", "soldier", "diffraction", "university", "observatory", 
        "residents", "followers", "members", "graduates", "students", "researchers",
        "unknown", "unnamed", "various", "family", "children", "grandchildren",
        "barack obama", "bryson dechambeau", "hegel's science", "x-ray", "logic",
        "nobel prize", "society", "association", "institute", "school", "college",
        "calculus", "biology", "physiology", "legacy", "tradition", "science of", 
        "novelty", "ship", "hms ", "temple", "government", "pupils", "uncle",
        "father", "mother", "sister", "brother", "wife", "husband", "son", "daughter",
        "physicists", "mathematicians", "revolutionaries", "group", "team"
    ]
    
    nodes_to_remove = []
    for node in graph.nodes():
        lower = node.lower()
        if any(k in lower for k in garbage_keywords):
            nodes_to_remove.append(node)
    
    if nodes_to_remove:
        graph.remove_nodes_from(nodes_to_remove)
        print(f"🗑️  Supprimé {len(nodes_to_remove)} intrus (Garbage Data).")

    # ==========================================
    # 2. STANDARDISATION DES NOMS (Normalization)
    # ==========================================
    mapping = {}
    
    # Titres à supprimer
    titles_pattern = r'^(Dr\.|Sir\s|Prof\.|Baron\s|Lord\s|Lady\s|Reverend\s|Rev\.|Father\s|Abbé\s|Canon\s|Privy Councillor\s|Don\s)'
    
    for node in graph.nodes():
        new_name = node
        
        # 1. Enlever les titres
        new_name = re.sub(titles_pattern, '', new_name, flags=re.IGNORECASE)
        
        # 2. Enlever les dates " (1800-1900)" ou " (b. 1800)"
        new_name = re.sub(r'\s*\([^)]*\d{4}[^)]*\)', '', new_name)  # (1899-1980) ou (b. 1888)
        new_name = re.sub(r'\s*\(\d{4}[–\-−]?\)', '', new_name)      # (1900-)
        
        # 3. Normaliser les apostrophes
        new_name = new_name.replace("’", "'")

        new_name = new_name.strip()

        if new_name != node and new_name:
            mapping[node] = new_name
            
    if mapping:
        print(f"✨  Standardisation de {len(mapping)} noms...")
        
        for old, new in mapping.items():
            if new in graph and new != old:
                # Collision -> Merge old into new
                try:
                    graph = nx.contracted_nodes(graph, new, old, self_loops=False)
                except:
                    pass
            elif new != old:
                # Rename if target doesn't exist
                try:
                    nx.relabel_nodes(graph, {old: new}, copy=False)
                except KeyError:
                     pass
                except Exception:
                     pass

    # ==========================================
    # 3. FUSION DES DOUBLONS (Canonicalization)
    # ==========================================
    
    # 3.1 Mapping explicite (Utilisateur + Analysé)
    explicit_merges = {
        "J. D. Bernal": "John Desmond Bernal",
        "John Bernal": "John Desmond Bernal",
        "J.J. Thomson": "Joseph John Thomson",
        "J. J. Thomson": "Joseph John Thomson",
        "Isidor I. Rabi": "Isidor Isaac Rabi",
        "I. I. Rabi": "Isidor Isaac Rabi",
        "Nicolas Léonard Sadi Carnot": "Sadi Carnot",
        "Wilhelm Maximilian Wundt": "Wilhelm Wundt",
        "Thomas Alva Edison": "Thomas Edison",
        
        # Nouveaux ajouts V4
        "J. Robert Oppenheimer": "Robert Oppenheimer",
        "W. H. Bragg": "William Henry Bragg",
        "W.H. Bragg": "William Henry Bragg",
        "Franz S. Exner": "Franz Serafin Exner",
        "Franz-Serafin Exner": "Franz Serafin Exner",
        "Ronald G.W. Norrish": "Ronald George Wreyford Norrish",
        "Ronald G. W. Norrish": "Ronald George Wreyford Norrish",
        "Jacobus Henricus van 't Hoff": "Jacobus Henricus van 't Hoff", 
        "H. G. Wells": "H.G. Wells",
        "J. B. S. Haldane": "J.B.S. Haldane",
    }
    
    print("🔗  Fusion des doublons connus...")
    for alias, canonical in explicit_merges.items():
        # Check standardisation d'apostrophe
        alias = alias.replace("’", "'")
        canonical = canonical.replace("’", "'")
        
        if alias in graph and canonical in graph and alias != canonical:
            print(f"   - Fusion: {alias} -> {canonical}")
            try:
                graph = nx.contracted_nodes(graph, canonical, alias, self_loops=False)
            except:
                pass
        elif alias in graph and canonical not in graph:
             nx.relabel_nodes(graph, {alias: canonical}, copy=False)

    # 3.2 Fusion Heuristique (Initiales)
    print("🤖  Fusion heuristique (V4 - Safe Mode)...")
    
    # On reconstruit la map car les noms ont changé
    last_name_map = collections.defaultdict(list)
    for node in graph.nodes():
        parts = node.split()
        if len(parts) >= 2:
            last = parts[-1]
            last_name_map[last].append(node)
            
    potential_merges = []
    
    for last, names in last_name_map.items():
        if len(names) < 2: continue
        names.sort(key=len, reverse=True)
        canonical = names[0]
        
        for other in names[1:]:
            c_parts = canonical.split()
            o_parts = other.split()
            
            # Condition stricte: length check
            if len(o_parts) > len(c_parts): continue
            
            # Condition stricte: Initiales matching
            match = True
            for i, o in enumerate(o_parts[:-1]):
                if i >= len(c_parts) - 1: # Protection index
                    match = False
                    break
                    
                c = c_parts[i]
                if o == c: continue # Full match part
                if len(o) <= 2 and o[0] == c[0]: continue # "J." or "J" matches "John"
                match = False
                break
            
            if match:
                 # RAFFINEMENT: Si 'other' (J. Smith) matche PLUSIEURS candidats potentiels, on NE FAIT RIEN.
                 matches_found = 0
                 for potential_c in names:
                     if potential_c == other: continue
                     pc_parts = potential_c.split()
                     if len(o_parts) > len(pc_parts): continue
                     p_match = True
                     for i, o in enumerate(o_parts[:-1]):
                         if i >= len(pc_parts) - 1:
                             p_match = False
                             break
                         c = pc_parts[i]
                         if o == c: continue
                         if len(o) <= 2 and o[0] == c[0]: continue
                         p_match = False
                         break
                     if p_match: matches_found += 1
                 
                 if matches_found == 1:
                     potential_merges.append((other, canonical))

    count_auto = 0
    for alias, canonical in potential_merges:
        if alias in graph and canonical in graph and alias != canonical:
            try:
                graph = nx.contracted_nodes(graph, canonical, alias, self_loops=False)
                count_auto += 1
            except:
                pass
    
    print(f"   (Fusionné {count_auto} items par heuristique)")

    # ==========================================
    # SAUVEGARDE
    # ==========================================
    final_nodes = graph.number_of_nodes()
    nx.write_gexf(graph, output_file)
    print("-" * 30)
    print("✅ POST-PROCESSING V4 TERMINÉ")
    print(f"Avant: {initial_nodes} -> Après: {final_nodes}")
    print(f"Graphe sauvegardé : {output_file}")

if __name__ == "__main__":
    post_process_graph()
