import wikipediaapi
from typing import Optional
from config import WIKIPEDIA_LANGUAGE

class WikipediaClient:
    def __init__(self):
        # User-Agent requis par Wikipedia API
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='StudentGraphProject/1.0 (contact@example.university.edu)',
            language=WIKIPEDIA_LANGUAGE
        )
    
    def get_scientist_text(self, name: str) -> tuple[Optional[str], list]:
        """
        Récupère le texte Wikipedia d'un scientifique.
        Retourne le résumé + début du contenu pour ne pas surcharger le LLM.
        """
        page = self.wiki.page(name)
        
        if not page.exists():
            return None
            
        # On construit un texte riche mais concis
        # 1. Le résumé est crucial (contient souvent les dates, nationalité, domaine)
        content = f"Titre: {page.title}\n\nRésumé:\n{page.summary}\n\n"
        
        # 2. On ajoute les 25000 premiers caractères (compromis Vitesse/Exhaustivité)
        # Lire tout le texte est trop lent et cause des timeouts.
        content += f"Détails:\n{page.text[:25000]}"
        
        # 3. Récupérer les liens (c'est très utile pour aider le LLM à identifier les noms corrects)
        links = list(page.links.keys())[:300]
        
        return content, links
    
    def page_exists(self, name: str) -> bool:
        """Vérifie si une page existe pour ce nom."""
        return self.wiki.page(name).exists()
    
    def get_scientific_field(self, name: str) -> Optional[str]:
        """
        Extrait le domaine scientifique à partir des catégories Wikipedia.
        Retourne le domaine principal (ex: 'Physics', 'Biology', 'Mathematics').
        """
        page = self.wiki.page(name)
        
        if not page.exists():
            return None
        
        # Dictionnaire de mapping catégories → domaines
        field_keywords = {
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
        
        # Récupérer les catégories
        categories = [cat.lower() for cat in page.categories.keys()]
        
        # Chercher le domaine qui matche le plus
        field_scores = {}
        for field, keywords in field_keywords.items():
            score = sum(1 for cat in categories for kw in keywords if kw in cat)
            if score > 0:
                field_scores[field] = score
        
        if field_scores:
            # Retourner le domaine avec le meilleur score
            return max(field_scores, key=field_scores.get)
        
        return None
    
    def extract_years(self, name: str) -> tuple[Optional[int], Optional[int]]:
        """
        Extract birth and death years from Wikipedia page.
        Uses regex on summary and categories.
        Returns (birth_year, death_year) or None values if not found.
        """
        import re
        
        page = self.wiki.page(name)
        
        if not page.exists():
            return None, None
        
        birth_year = None
        death_year = None
        
        summary = page.summary
        
        # Common patterns for dates in Wikipedia summaries
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
            
            # "1879 births"
            birth_cat = re.search(r'(\d{4})\s*births?', cat_lower)
            if birth_cat:
                birth_year = int(birth_cat.group(1))
            
            # "1955 deaths"
            death_cat = re.search(r'(\d{4})\s*deaths?', cat_lower)
            if death_cat:
                death_year = int(death_cat.group(1))
        
        return birth_year, death_year
