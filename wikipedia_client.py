import wikipediaapi
import wikipedia
from typing import Optional
from config import WIKIPEDIA_LANGUAGE

class WikipediaClient:
    def __init__(self):
        # User-Agent requis par Wikipedia API
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='StudentGraphProject/1.0 (contact@example.university.edu)',
            language=WIKIPEDIA_LANGUAGE
        )
        # Configurer la langue pour la recherche fuzzy
        wikipedia.set_lang(WIKIPEDIA_LANGUAGE)
    
    def get_scientist_text(self, name: str) -> tuple[Optional[str], list]:
        """
        Récupère le texte Wikipedia d'un scientifique.
        Utilise une recherche fuzzy pour trouver la bonne page.
        Retourne le résumé + début du contenu pour ne pas surcharger le LLM.
        """
        # 1. Recherche floue (Fuzzy Search) pour trouver le vrai titre
        best_match = name
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                candidate = search_results[0]
                
                # Validation ANTI-VOL D'IDENTITÉ 🛡️
                # Si le nom original est "Humphrey Newton" et le résultat est "Isaac Newton",
                # c'est probablement faux. On vérifie la similarité.
                import difflib
                similarity = difflib.SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
                
                # Seuil de tolérance :
                # - Si > 0.6 : C'est probablement une correction typo ou Prénom manquant (Curie -> Marie Curie)
                # - Si < 0.6 : C'est suspect (Humphrey Newton -> Isaac Newton = 0.5)
                
                if similarity > 0.6 or (name in candidate or candidate in name):
                    best_match = candidate
                    if best_match != name:
                         print(f"  ✨ Correction: '{name}' -> '{best_match}' (Sim: {similarity:.2f})")
                else:
                    print(f"  ⚠️ Correction rejetée: '{name}' -> '{candidate}' (Trop différent, Sim: {similarity:.2f})")
                    best_match = name # On garde le nom original pour tenter le coup ou échouer proprement
            
        except Exception as e:
            print(f"  ⚠️ Erreur recherche fuzzy: {e}. Essai avec le nom brut.")
            best_match = name

        # 2. Chargement de la page avec le titre exact
        page = self.wiki.page(best_match)
        
        # Validation ANTI-CONCEPT 🛡️
        # Si le titre de la page contient "method", "theorem", "law", etc., ce n'est pas une personne.
        from config import EXCLUSION_PATTERNS
        import re
        
        if page.exists():
            for pattern in EXCLUSION_PATTERNS:
                if re.search(pattern, page.title, re.IGNORECASE):
                     print(f"  🚫 Rejet: La page '{page.title}' semble être un concept, pas une personne.")
                     return None
        
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
    
    def is_scientist(self, name: str) -> bool:
        """
        Vérifie si une personne est un scientifique via les catégories Wikipedia.
        Retourne True si c'est un scientifique, False sinon.
        """
        # Recherche fuzzy pour trouver la bonne page
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                name = search_results[0]
        except:
            pass

        page = self.wiki.page(name)
        
        if not page.exists():
            return True  # Fail open si la page n'existe pas (sera filtré plus tard)
        
        # Racines de mots qui indiquent un scientifique (matchent singulier ET pluriel)
        # Ex: 'physic' match 'physicist', 'physicists', 'physics'
        # NOTE: 'philosoph' trop large (inclut Gandhi) - on limite aux philosophes des sciences
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
            # Philosophes des sciences spécifiquement
            'philosophy of science', 'analytic philosoph', 'philosophy of mind',
            'philosophy of math', 'epistemolog'
        ]
        
        # Racines qui excluent (définitivement pas un scientifique)
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
        
        # Récupérer les catégories
        categories = [cat.lower() for cat in page.categories.keys()]
        categories_text = ' '.join(categories)
        
        # PRIORITÉ AUX SCIENTIFIQUES : si on trouve une catégorie scientifique, on accepte
        # Cela permet à des scientifiques ayant aussi servi dans l'armée (ex: Poincaré) d'être inclus
        for stem in SCIENTIST_STEMS:
            if stem in categories_text:
                return True
        
        # Si pas de catégorie scientifique, vérifier les exclusions
        for exclude in EXCLUDE_STEMS:
            if exclude in categories_text:
                return False
        
        # Si aucun match, on accepte par défaut (fail open)
        # Cela permet d'inclure des scientifiques moins connus
        return True
    
    def get_scientific_field(self, name: str) -> Optional[str]:
        """
        Extrait le domaine scientifique à partir des catégories Wikipedia.
        Retourne le domaine principal (ex: 'Physics', 'Biology', 'Mathematics').
        """
        # Recherche fuzzy ici aussi pour être cohérent
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                name = search_results[0]
        except:
            pass

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
        
        # Recherche fuzzy ici aussi
        try:
            search_results = wikipedia.search(name, results=1)
            if search_results:
                name = search_results[0]
        except:
            pass

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
