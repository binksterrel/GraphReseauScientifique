# Configuration du projet Graphe d'Influence Scientifique

# ============================================================
# CONFIGURATION LLM
# ============================================================

# Clé API OpenAI (laisser vide si vous utilisez Ollama)
OPENAI_API_KEY = ""

# True = utiliser Ollama (gratuit, local)
# False = utiliser OpenAI (payant, nécessite clé API)
USE_OLLAMA = False

# Configuration Groq (API Rapide)
USE_GROQ = True
GROQ_API_KEY = "" # Set via environment variable
GROQ_MODEL = "llama-3.3-70b-versatile"

# Configuration Mistral (API)
USE_MISTRAL = False
MISTRAL_API_KEY = ""
MISTRAL_MODEL = "mistral-large-latest"
MISTRAL_API_URL = "https://api.mistral.ai"

# Configuration Cerebras (API Ultra Rapide)
USE_CEREBRAS = False
CEREBRAS_API_KEY = ""
CEREBRAS_MODEL = "gpt-oss-120b"
CEREBRAS_API_URL = "https://api.cerebras.ai/v1"

# Configuration Ollama
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "mistral"  # ou "llama2", "codellama", etc.

# ============================================================
# PARAMÈTRES DE L'ALGORITHME
# ============================================================

# Profondeur maximale de récursion (3-4 recommandé)
MAX_DEPTH = 6

# Nombre maximum de scientifiques à analyser
MAX_SCIENTISTS = 500

# Scientifique de départ
START_SCIENTIST = "Albert Einstein"

# Langue Wikipedia ('fr' pour français, 'en' pour anglais)
WIKIPEDIA_LANGUAGE = "en"

# ============================================================
# LISTE NOIRE (personnes à exclure du graphe)
# ============================================================
BLACKLIST = [
    # Personnages politiques/dictateurs
    "Hitler",
    "Stalin",
    "Mussolini",
    "Mao",
    
    # Autres non-scientifiques fréquemment liés par erreur
    "Napoleon",
    "Jesus",
    "Muhammad",
    "Buddha",
]
