import networkx as nx
import os
import re
import time
from collections import deque
from typing import Tuple, Optional, Deque

from wikipedia_client import WikipediaClient
from llm_extractor import LLMExtractor
from config import MAX_DEPTH, MAX_SCIENTISTS, BLACKLIST, EXCLUSION_PATTERNS
from logger import get_logger

logger = get_logger(__name__)


class GraphBuilder:
    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.wiki_client = WikipediaClient()
        self.llm = LLMExtractor()
        self.visited: set[str] = set()

    def build_influence_graph(self, start_scientist: str) -> nx.DiGraph:
        """
        Construit le graphe d'influence en utilisant un parcours BFS (Largeur d'abord).
        Reprend le travail existant si un fichier est trouvé.
        """
        filename = "output/scientist_graph.gexf"
        queue = self._load_existing_graph(filename, start_scientist)

        logger.info("DEMARRAGE de la construction du graphe")
        logger.info(f"Max Profondeur: {MAX_DEPTH} | Max Scientifiques: {MAX_SCIENTISTS}")

        while queue and len(self.visited) < MAX_SCIENTISTS:
            current_scientist, depth = queue.popleft()

            # 1. Vérifications préliminaires
            if current_scientist in self.visited:
                continue
            if depth > MAX_DEPTH:
                continue
            # Vérifier la liste noire
            if any(bl.lower() in current_scientist.lower() for bl in BLACKLIST):
                logger.warning(f"{current_scientist} est dans la liste noire. Ignore.")
                continue

            logger.info(f"[{len(self.visited)+1}/{MAX_SCIENTISTS}] Analyse de: {current_scientist} (Prof: {depth})")

            # 2. Récupération du texte
            try:
                result = self.wiki_client.get_scientist_text(current_scientist)
            except Exception as e:
                logger.error(f"Erreur critique recuperation Wikipedia ({e}). On passe au suivant.")
                continue

            if not result:
                logger.warning(f"Pas de page Wikipedia trouvee pour {current_scientist}. Ignore.")
                continue

            wiki_text, links = result
            logger.debug(f"{len(wiki_text)} caracteres recuperes. {len(links)} liens identifies.")

            # Extraction du domaine scientifique
            field: Optional[str] = None
            if current_scientist in self.graph.nodes:
                field = self.graph.nodes[current_scientist].get('field')

            if not field or field == 'Other':
                field = self.wiki_client.get_scientific_field(current_scientist)

            if not field:
                field = 'Other'

            # 3. Ajout/Maj au graphe et marquage comme visité
            self.visited.add(current_scientist)

            # Récupération de l'année de naissance si elle n'est pas déjà présente
            birth_year: Optional[int] = None
            if current_scientist in self.graph.nodes:
                birth_year = self.graph.nodes[current_scientist].get('birth_year')
            if not birth_year:
                birth_year, _ = self.wiki_client.extract_years(current_scientist)

            # On met à jour ou crée le nœud avec les attributs complets
            self.graph.add_node(current_scientist, depth=depth, field=field, birth_year=birth_year)

            # Si on atteint la profondeur max, on ne cherche pas les voisins
            if depth == MAX_DEPTH:
                continue

            # 4. Extraction des relations via LLM
            relations = self.llm.extract_relations(wiki_text, current_scientist, links=links)

            # 5. Traitement des "inspirations" (A a inspiré current)
            inspirations = relations.get('inspired_by', [])
            for person in inspirations:
                if person == current_scientist:
                    continue
                if self._is_valid_name(person):
                    if self._is_chronologically_valid(current_scientist, person, "inspired_by"):
                        self.graph.add_edge(person, current_scientist, relation="inspired")
                        if person not in self.visited:
                            queue.append((person, depth + 1))

            # 6. Traitement des "inspirés" (current a inspiré B)
            inspired_list = relations.get('inspired', [])
            for person in inspired_list:
                if person == current_scientist:
                    continue
                if self._is_valid_name(person):
                    if self._is_chronologically_valid(current_scientist, person, "inspired"):
                        self.graph.add_edge(current_scientist, person, relation="inspired")
                        if person not in self.visited:
                            queue.append((person, depth + 1))

            logger.info(f"Relations: {len(inspirations)} inspirations, {len(inspired_list)} inspires.")

            # Petite pause pour être poli envers les APIs
            time.sleep(0.5)

            # --- AUTOSAVE ---
            if len(self.visited) % 20 == 0:
                logger.info(f"Autosave: Sauvegarde intermediaire ({len(self.visited)} noeuds)...")
                self.save_graph(filename)

        logger.info("CONSTRUCTION TERMINEE")
        logger.info(f"Total Noeuds: {self.graph.number_of_nodes()}")
        logger.info(f"Total Aretes: {self.graph.number_of_edges()}")

        return self.graph

    def _is_chronologically_valid(self, current_node: str, target_node: str, relation_type: str) -> bool:
        """
        Vérifie la cohérence temporelle d'une relation.

        Logique:
        - inspired_by (target -> current): Target doit être né AVANT ou MEME TEMPS que Current.
        - inspired (current -> target): Target doit être né APRES ou MEME TEMPS que Current.

        Marge d'erreur de 5 ans pour les contemporains.
        Si une date manque, on laisse passer (fail open).
        """
        # 1. Obtenir l'année de naissance du nœud courant
        current_birth: Optional[int] = self.graph.nodes[current_node].get('birth_year')
        if not current_birth:
            current_birth, _ = self.wiki_client.extract_years(current_node)
            if current_birth:
                self.graph.nodes[current_node]['birth_year'] = current_birth

        # 2. Obtenir l'année de naissance du nœud cible
        target_birth: Optional[int] = None
        if target_node in self.graph.nodes:
            target_birth = self.graph.nodes[target_node].get('birth_year')

        if not target_birth:
            target_birth, _ = self.wiki_client.extract_years(target_node)

        # 3. Validation (Fail Open)
        if not current_birth or not target_birth:
            return True

        margin = 5

        if relation_type == "inspired_by":
            if target_birth > (current_birth + margin):
                logger.warning(
                    f"Anachronisme rejete: {target_node} ({target_birth}) "
                    f"ne peut pas avoir inspire {current_node} ({current_birth})"
                )
                return False

        elif relation_type == "inspired":
            if target_birth < (current_birth - margin):
                logger.warning(
                    f"Anachronisme rejete: {current_node} ({current_birth}) "
                    f"ne peut pas avoir inspire {target_node} ({target_birth})"
                )
                return False

        return True

    def _load_existing_graph(self, filename: str, start_scientist: str) -> Deque[Tuple[str, int]]:
        """Tente de charger un graphe existant et reconstruit la file d'attente."""
        queue: Deque[Tuple[str, int]] = deque([(start_scientist, 0)])

        if os.path.exists(filename):
            logger.info(f"Reprise du graphe existant: {filename}")
            try:
                self.graph = nx.read_gexf(filename)
                logger.info(
                    f"Graphe charge: {self.graph.number_of_nodes()} noeuds, "
                    f"{self.graph.number_of_edges()} aretes"
                )

                queue_candidates: dict[str, float] = {}

                for node, data in self.graph.nodes(data=True):
                    if 'depth' in data:
                        self.visited.add(node)
                    else:
                        queue_candidates[node] = float('inf')

                # Calculer la profondeur des candidats basée sur leurs voisins visités
                for u, v in self.graph.edges():
                    if u in self.visited and v in queue_candidates:
                        parent_depth = self.graph.nodes[u].get('depth', 0)
                        if isinstance(parent_depth, str):
                            parent_depth = int(parent_depth)
                        queue_candidates[v] = min(queue_candidates[v], parent_depth + 1)

                    if u in queue_candidates and v in self.visited:
                        parent_depth = self.graph.nodes[v].get('depth', 0)
                        if isinstance(parent_depth, str):
                            parent_depth = int(parent_depth)
                        queue_candidates[u] = min(queue_candidates[u], parent_depth + 1)

                valid_candidates = [
                    (n, int(d)) for n, d in queue_candidates.items()
                    if d != float('inf')
                ]
                valid_candidates.sort(key=lambda x: x[1])

                queue = deque(valid_candidates)
                logger.info(
                    f"Reprise: {len(self.visited)} noeuds visites, "
                    f"{len(queue)} dans la file d'attente."
                )

            except Exception as e:
                logger.error(f"Erreur lors de la reprise du graphe: {e}")
                logger.warning("Demarrage d'un nouveau graphe.")
                self.graph = nx.DiGraph()
                queue = deque([(start_scientist, 0)])

        if not queue and len(self.visited) == 0:
            queue = deque([(start_scientist, 0)])

        return queue

    def _is_valid_name(self, name: str) -> bool:
        """Filtre pour s'assurer que le nom est celui d'un scientifique valide."""
        if not name or not isinstance(name, str):
            return False

        # Doit faire au moins 3 caractères et contenir un espace (Prénom Nom)
        if len(name) < 3 or ' ' not in name:
            return False

        # Vérifier la liste noire directe
        if any(bl.lower() in name.lower() for bl in BLACKLIST):
            return False

        # Vérifier les patterns d'exclusion (regex)
        for pattern in EXCLUSION_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return False

        # Auto-vérification via catégories Wikipedia
        if not self.wiki_client.is_scientist(name):
            logger.debug(f"Auto-rejet: '{name}' n'est pas un scientifique (categories Wikipedia)")
            return False

        return True

    def save_graph(self, filename: str = "output/scientist_graph.gexf") -> None:
        """Exporte le graphe pour Gephi."""
        try:
            # Nettoyage des attributs None avant export
            export_graph = self.graph.copy()
            for _, data in export_graph.nodes(data=True):
                for key, value in list(data.items()):
                    if value is None:
                        if key == 'birth_year':
                            data[key] = 0
                        else:
                            data[key] = ""

            nx.write_gexf(export_graph, filename)
            logger.info(f"Graphe exporte vers: {filename}")
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
