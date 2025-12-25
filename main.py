from graph_builder import GraphBuilder
from graph_analyzer import GraphAnalyzer
from visualizer import GraphVisualizer
from llm_extractor import LLMExtractor
from config import START_SCIENTIST
import os
import sys

def main():
    print("="*60)
    print("🔬 PROJET GRAPHE D'INFLUENCE SCIENTIFIQUE")
    print("="*60)
    
    # 0. Préparation
    os.makedirs("output", exist_ok=True)
    
    # Vérification Health Check LLM
    if not LLMExtractor().check_connection():
        print("\n" + "="*60)
        print("🛑 ERREUR CRITIQUE : LLM INTROUVABLE")
        print("="*60)
        # Note: Plus besoin de conseils spécifiques ici, check_connection() est verbeux
        return
    
    # 1. Construction
    builder = GraphBuilder()
    try:
        graph = builder.build_influence_graph(START_SCIENTIST)
    except KeyboardInterrupt:
        print("\n🛑 Interruption utilisateur. Sauvegarde partielle...")
        graph = builder.graph
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        print("💾 Sauvegarde d'urgence des données graph...")
        builder.save_graph("output/scientist_graph.gexf")
        return

    if graph.number_of_nodes() == 0:
        print("❌ Aucun nœud récupéré.")
        return

    # 2. Export données brutes
    builder.save_graph("output/scientist_graph.gexf")
    
    # 3. Analyse
    analyzer = GraphAnalyzer(graph)
    analyzer.analyze()
    
    # 4. Visualisation
    visualizer = GraphVisualizer(graph)
    visualizer.create_interactive_html("output/graph.html")
    
    print("\n✅ Terminé avec succès!")

if __name__ == "__main__":
    # Vérification des dépendances au lancement
    try:
        import wikipediaapi
        import networkx
        import pyvis
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("   Exécutez: pip install -r requirements.txt")
        sys.exit(1)
        
    main()
