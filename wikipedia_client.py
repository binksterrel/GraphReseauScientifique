import re
import difflib
from typing import Optional

import wikipediaapi
import wikipedia

from config import WIKIPEDIA_LANGUAGE, EXCLUSION_PATTERNS
from logger import get_logger

logger = get_logger(__name__)


class WikipediaClient:
    def __init__(self) -> None:
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='StudentGraphProject/1.0 (contact@example.university.edu)',
            language=WIKIPEDIA_LANGUAGE
        )
        wikipedia.set_lang(WIKIPEDIA_LANGUAGE)

    def get_scientist_text(self, name: str) -> Optional[tuple[str, list[str]]]:
        """
        Récupère le texte Wikipedia d'un scientifique.
        Utilise une recherche fuzzy pour trouver la bonne page.
        Retourne le résumé + début du contenu pour ne pas surcharger le LLM.
        """
        best_match = name
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                candidate = search_results[0]

                similarity = difflib.SequenceMatcher(
                    None, name.lower(), candidate.lower()
                ).ratio()

                if similarity > 0.6 or (name in candidate or candidate in name):
                    best_match = candidate
                    if best_match != name:
                        logger.debug(
                            f"Correction: '{name}' -> '{best_match}' (Sim: {similarity:.2f})"
                        )
                else:
                    logger.debug(
                        f"Correction rejetee: '{name}' -> '{candidate}' "
                        f"(Trop different, Sim: {similarity:.2f})"
                    )
                    best_match = name

        except Exception as e:
            logger.warning(f"Erreur recherche fuzzy: {e}. Essai avec le nom brut.")
            best_match = name

        page = self.wiki.page(best_match)

        if page.exists():
            for pattern in EXCLUSION_PATTERNS:
                if re.search(pattern, page.title, re.IGNORECASE):
                    logger.debug(
                        f"Rejet: La page '{page.title}' semble etre un concept, pas une personne."
                    )
                    return None

        if not page.exists():
            return None

        content = f"Titre: {page.title}\n\nRésumé:\n{page.summary}\n\n"
        content += f"Détails:\n{page.text[:25000]}"

        links = list(page.links.keys())[:300]

        return content, links

    def page_exists(self, name: str) -> bool:
        """Vérifie si une page existe pour ce nom."""
        return self.wiki.page(name).exists()

    def is_scientist(self, name: str) -> bool:
        """
        Vérifie si une personne est un scientifique via les catégories Wikipedia.
        Retourne True si c'est un scientifique, False sinon.
        """
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                name = search_results[0]
        except Exception:
            pass

        page = self.wiki.page(name)

        if not page.exists():
            return True  # Fail open

        SCIENTIST_STEMS = [
            'physic', 'chemi', 'mathematic', 'biolog', 'astronom',
            'engineer', 'computer scien', 'genetic', 'geolog',
            'neuroscien', 'biochem', 'astrophysic', 'pharmacolog',
            'microbiolog', 'ecolog', 'botan', 'zoolog',
            'crystallograph', 'immunolog', 'virolog', 'inventor',
            'logician', 'statistic', 'epidemiolog',
            'paleontolog', 'anatom', 'physiolog', 'patholog',
            'naturalist', 'cosmolog', 'oceanograph', 'meteorolog',
            'scientist', 'women in science', 'nobel laureate',
            'philosophy of science', 'analytic philosoph', 'philosophy of mind',
            'philosophy of math', 'epistemolog'
        ]

        EXCLUDE_STEMS = [
            'actor', 'actress', 'film director', 'screenwriter', 'television',
            'singer', 'musician', 'composer', 'rapper', 'songwriter',
            'politician', 'diplomat', 'monarch', 'king of', 'queen of', 'emperor',
            'military', 'general of', 'admiral', 'colonel', 'soldier',
            'president of', 'prime minister', 'governors of', 'senator', 'minister of',
            'journalist', 'editor', 'newspaper', 'broadcaster',
            'novelist', 'poet', 'playwright', 'literary',
            'athlete', 'footballer', 'cricketer', 'basketball', 'tennis player',
            'religious leader', 'bishop', 'cardinal', 'pope', 'imam', 'rabbi',
            'businesspeople', 'entrepreneur', 'banker',
            'criminal', 'murderer', 'revolutionary leader'
        ]

        categories = [cat.lower() for cat in page.categories.keys()]
        categories_text = ' '.join(categories)

        for stem in SCIENTIST_STEMS:
            if stem in categories_text:
                return True

        for exclude in EXCLUDE_STEMS:
            if exclude in categories_text:
                return False

        return True

    def get_scientific_field(self, name: str) -> Optional[str]:
        """
        Extrait le domaine scientifique à partir des catégories Wikipedia.
        Retourne le domaine principal (ex: 'Physics', 'Biology', 'Mathematics').
        """
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                name = search_results[0]
        except Exception:
            pass

        page = self.wiki.page(name)

        if not page.exists():
            return None

        field_keywords: dict[str, list[str]] = {
            'Physics': ['physicist', 'physics', 'quantum', 'relativity', 'thermodynamics'],
            'Mathematics': ['mathematician', 'mathematics', 'geometry', 'algebra', 'topology'],
            'Chemistry': ['chemist', 'chemistry', 'chemical', 'molecule'],
            'Biology': ['biologist', 'biology', 'evolution', 'genetics', 'botany', 'zoology'],
            'Computer Science': ['computer scientist', 'computer science', 'programming', 'algorithm'],
            'Medicine': ['physician', 'medical', 'medicine', 'anatomist'],
            'Astronomy': ['astronomer', 'astronomy', 'astrophysics', 'cosmology'],
            'Engineering': ['engineer', 'engineering'],
            'Philosophy': ['philosopher', 'philosophy'],
            'Economics': ['economist', 'economics']
        }

        categories = [cat.lower() for cat in page.categories.keys()]

        field_scores: dict[str, int] = {}
        for field, keywords in field_keywords.items():
            score = sum(1 for cat in categories for kw in keywords if kw in cat)
            if score > 0:
                field_scores[field] = score

        if field_scores:
            return max(field_scores, key=field_scores.get)  # type: ignore

        return None

    def extract_years(self, name: str) -> tuple[Optional[int], Optional[int]]:
        """
        Extract birth and death years from Wikipedia page.
        Uses regex on summary and categories.
        Returns (birth_year, death_year) or None values if not found.
        """
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                name = search_results[0]
        except Exception:
            pass

        page = self.wiki.page(name)

        if not page.exists():
            return None, None

        birth_year: Optional[int] = None
        death_year: Optional[int] = None

        summary = page.summary

        # Pattern 1: "(1879–1955)" or "(1879-1955)"
        date_pattern = r'\((\d{4})\s*[–\-−]\s*(\d{4})\)'
        match = re.search(date_pattern, summary)
        if match:
            birth_year = int(match.group(1))
            death_year = int(match.group(2))
            return birth_year, death_year

        # Pattern 2: "born 1879" or "b. 1879"
        birth_pattern = r'(?:born|b\.)\s*(\d{4})'
        match = re.search(birth_pattern, summary, re.IGNORECASE)
        if match:
            birth_year = int(match.group(1))

        # Pattern 3: "died 1955" or "d. 1955"
        death_pattern = r'(?:died|d\.)\s*(\d{4})'
        match = re.search(death_pattern, summary, re.IGNORECASE)
        if match:
            death_year = int(match.group(1))

        # Pattern 4: Look in categories for birth/death years
        categories = list(page.categories.keys())
        for cat in categories:
            cat_lower = cat.lower()

            birth_cat = re.search(r'(\d{4})\s*births?', cat_lower)
            if birth_cat:
                birth_year = int(birth_cat.group(1))

            death_cat = re.search(r'(\d{4})\s*deaths?', cat_lower)
            if death_cat:
                death_year = int(death_cat.group(1))

        return birth_year, death_year
