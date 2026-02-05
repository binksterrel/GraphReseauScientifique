# Configuration du projet Graphe d'Influence Scientifique

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# ============================================================
# CONFIGURATION LLM
# ============================================================

# Clé API OpenAI (laisser vide si vous utilisez Ollama)
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")

# True = utiliser Ollama (gratuit, local)
# False = utiliser OpenAI (payant, nécessite clé API)
USE_OLLAMA: bool = os.environ.get("USE_OLLAMA", "true").lower() == "true"

# Configuration Groq (API Rapide)
USE_GROQ: bool = os.environ.get("USE_GROQ", "false").lower() == "true"
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Configuration Mistral (API)
USE_MISTRAL: bool = os.environ.get("USE_MISTRAL", "false").lower() == "true"
MISTRAL_API_KEY: str = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_MODEL: str = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")
MISTRAL_API_URL: str = os.environ.get("MISTRAL_API_URL", "https://api.mistral.ai")

# Configuration Cerebras (API Ultra Rapide)
USE_CEREBRAS: bool = os.environ.get("USE_CEREBRAS", "false").lower() == "true"
CEREBRAS_API_KEY: str = os.environ.get("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL: str = os.environ.get("CEREBRAS_MODEL", "gpt-oss-120b")
CEREBRAS_API_URL: str = os.environ.get("CEREBRAS_API_URL", "https://api.cerebras.ai/v1")

# Configuration Ollama
OLLAMA_URL: str = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "mistral")

# ============================================================
# PARAMÈTRES DE L'ALGORITHME
# ============================================================

# Profondeur maximale de récursion (3-4 recommandé)
MAX_DEPTH: int = int(os.environ.get("MAX_DEPTH", "15"))

# Nombre maximum de scientifiques à analyser
MAX_SCIENTISTS: int = int(os.environ.get("MAX_SCIENTISTS", "1000"))

# Scientifique de départ
START_SCIENTIST: str = os.environ.get("START_SCIENTIST", "Albert Einstein")

# Langue Wikipedia ('fr' pour français, 'en' pour anglais)
WIKIPEDIA_LANGUAGE: str = os.environ.get("WIKIPEDIA_LANGUAGE", "en")

# ============================================================
# LISTE NOIRE (personnes à exclure du graphe)
# ============================================================
BLACKLIST: list[str] = [
    # Personnages politiques/dictateurs/militaires
    "Hitler", "Stalin", "Mussolini", "Mao", "Napoleon",
    "European Organization for Nuclear Research", "CERN",
    "Devesh Sharma", # Chercheur moderne hors contexte historique
    "Not specified in the text", "Unknown students", "Future scientists", "All rights reserved",
    "Many physicists", "European intellectuals", "French Catholic Church",
    "Lenin", "Trotsky", "Marx", "Engels", "Queen Victoria",
    "Chief Justice", "President", "Prime Minister", "General",

    # Juristes / Politiques US fréquents
    "Rehnquist", "William Rehnquist",
    "Robert H. Jackson", "Jackson",
    "Scalia", "Ginsburg",
    "Pothan Joseph", # Journaliste
    "Gabriel Wigner", # Hallucination probable (Mix Gabriel Dirac / Eugene Wigner)
    "Fyodor Dostoyevsky", "Charles Dickens", "Albert Camus", "François-René de Chateaubriand",
    "Napoleon Bonaparte", "Russian Tsarina Elizabeth Alexeievna",
    "Writer", "Novelist", "Diplomat",  # "Philosopher" retiré - philosophes des sciences autorisés
    "Journalist", "Editor",

    # Autres non-scientifiques fréquemment liés par erreur
    "Jesus", "Muhammad", "Buddha", "God",
]

# ============================================================
# PATTERNS D'EXCLUSION (regex pour filtrer automatiquement)
# ============================================================
EXCLUSION_PATTERNS: list[str] = [
    # Groupes/Mouvements (terminaisons)
    r"ists$",           # e.g., "Cognitive scientists", "Logical positivists"
    r"ism$",            # e.g., "Logical positivism", "Western Marxism"
    r"economists$",     # e.g., "Classical economists"
    r"socialists$",     # e.g., "Utopian socialists"
    r"theorists$",      # e.g., "communist theorists"
    r"philosophers$",   # e.g., "Early analytic philosophers"

    # Organisations/Institutions
    r"\bUniversity\b",  # e.g., "University of Innsbruck"
    r"\bInstitute\b",   # e.g., "Adam Smith Institute"
    r"\bCollege\b",
    r"\bAcademy\b",
    r"\bSociety\b",     # e.g., "Adam Smith Society"
    r"\bLaboratory\b",  # e.g., "TRIUMF laboratory"
    r"\bFoundation\b",
    r"\bCompany\b",
    r"\bCorporation\b",
    r"\bCourt\b",       # e.g., "Supreme Court"

    # Mouvements/Concepts philosophiques/scientifiques (PAS des gens)
    r"\bCircle$",       # e.g., "Vienna Circle"
    r"\bSchool$",       # e.g., "Budapest School", "Stanford School"
    r"\bMovement\b",    # e.g., "Freethought movement"
    r"\bpsychology$",   # e.g., "Gestalt psychology"
    r"\bmethod$",       # e.g., "Gauss-Seidel method"
    r"\btheorem$",      # e.g., "Pythagorean theorem"
    r"\bequation$",     # e.g., "Schrodinger equation"
    r"\bprinciple$",    # e.g., "Uncertainty principle"
    r"\blaw$",          # e.g., "Newton's law"
    r"\beffect$",       # e.g., "Doppler effect"
    r"\bconstant$",     # e.g., "Planck constant"

    # Titres et prefixes indésirables
    r"^Chief Justice",
    r"^Justice",
    r"^President",
    r"^General",

    # Textes descriptifs (pas des noms propres)
    r"^members from",   # e.g., "members from SNOLAB"
    r"professor at",    # e.g., "first-year physics professor at..."
    r"^first-year",
]
