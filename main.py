import os
import sys

from graph_builder import GraphBuilder
from graph_analyzer import GraphAnalyzer
from visualizer import GraphVisualizer
from llm_extractor import LLMExtractor
from config import START_SCIENTIST
from logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("=" * 60)
    logger.info("EPISTEME NETWORK : PROJET GRAPHE D'INFLUENCE SCIENTIFIQUE")
    logger.info("=" * 60)

    # 0. Préparation
    os.makedirs("output", exist_ok=True)

    # Vérification Health Check LLM
    if not LLMExtractor().check_connection():
        logger.error("=" * 60)
        logger.error("ERREUR CRITIQUE : LLM INTROUVABLE")
        logger.error("=" * 60)
        return

    # 1. Construction
    builder = GraphBuilder()
    try:
        graph = builder.build_influence_graph(START_SCIENTIST)
    except KeyboardInterrupt:
        logger.warning("Interruption utilisateur. Sauvegarde partielle...")
        graph = builder.graph
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        logger.info("Sauvegarde d'urgence des donnees graph...")
        builder.save_graph("output/scientist_graph.gexf")
        return

    if graph.number_of_nodes() == 0:
        logger.error("Aucun noeud recupere.")
        return

    # 2. Export données brutes
    builder.save_graph("output/scientist_graph.gexf")

    # 3. Analyse
    analyzer = GraphAnalyzer(graph)
    analyzer.analyze()
    analyzer.save_results("output/analysis.json")
    analyzer.generate_small_world_html(
        template_path="docs/small_world.html",
        output_path="output/small_world.html",
    )

    # 4. Visualisation
    visualizer = GraphVisualizer(graph)
    visualizer.create_interactive_html("output/graph.html")

    logger.info("Termine avec succes!")


if __name__ == "__main__":
    # Vérification des dépendances au lancement
    try:
        import wikipediaapi
        import networkx
        import pyvis
    except ImportError as e:
        logger.error(f"Dependance manquante: {e}")
        logger.error("Executez: pip install -r requirements.txt")
        sys.exit(1)

    main()
