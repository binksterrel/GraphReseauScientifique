# 🔬 RÉSEAU SCIENTIFIQUE

Un outil interactif pour **générer, visualiser et analyser** les connexions entre scientifiques à partir de leurs pages Wikipédia, propulsé par l'Intelligence Artificielle.

![Aperçu du Graphe](output/preview.png)

## 🌟 Fonctionnalités

### Extraction et Analyse

*   **Extraction automatique** : Analyse des pages Wikipédia via LLM (Groq, OpenAI, Ollama, Mistral, Cerebras) pour trouver qui a influencé qui.
*   **Prompt Few-Shot + Chain-of-Thought** : Prompts avancés avec exemples et raisonnement structuré pour une meilleure précision.
*   **Cache intelligent** : Système de cache avec versioning pour éviter les appels LLM redondants.
*   **Validation Wikidata** : Vérification croisée des relations extraites via l'API SPARQL de Wikidata.

### Visualisation Interactive

*   **Graphe dynamique** : Zoom, recherche, glisser-déposer des nœuds.
*   **Filtres avancés** :
    *   Par **domaine scientifique** (Physique, Mathématiques, Chimie, etc.)
    *   Par **époque** (curseurs pour années de naissance/mort, 1400-2000)
*   **Chemin le plus court** : Animation "fourmis" pour visualiser le lien entre deux scientifiques.
*   **Données temporelles** : Années de naissance et mort affichées pour chaque scientifique.

### Algorithmes de Graphe

*   **PageRank** : Taille des nœuds selon leur influence globale dans le réseau.
*   **Détection de communautés** : Couleurs selon les "écoles de pensée" (algorithme de Louvain).
*   **Poids temporels** : Les arêtes sont pondérées selon la proximité temporelle des scientifiques liés.

### Analyse Avancée

*   **Détection des révolutionnaires** : Identification des "paradigm shifters" via l'analyse des trous structurels (constraint de Burt).
*   **Prédiction de liens** : Suggestion de relations manquantes basée sur les métriques de similarité (Jaccard, Adamic-Adar).
*   **Comparaison des traditions** : Analyse comparative des différentes écoles scientifiques (Grèce Antique, Lumières, etc.).

## 🚀 Installation

**Pré-requis** : Python 3.9+

1.  **Cloner ou télécharger le dossier du projet.**

2.  **Créer un environnement virtuel (recommandé) :**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    # ou .venv\Scripts\activate  # Windows
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

Ouvrez le fichier `config.py` pour ajuster les paramètres :

### Choix du LLM
| Variable | Fournisseur | Description |
|----------|-------------|-------------|
| `USE_GROQ = True` | Groq | Recommandé (300+ tokens/s) |
| `USE_OLLAMA = True` | Ollama | Exécution locale gratuite |
| `USE_OPENAI = True` | OpenAI | GPT-3.5/4 |
| `USE_MISTRAL = True` | Mistral AI | Alternative européenne |
| `USE_CEREBRAS = True` | Cerebras | Très rapide |

### Limites du Graphe
*   `MAX_DEPTH` : Profondeur d'exploration depuis le point de départ (ex: 6).
*   `MAX_SCIENTISTS` : Nombre maximum de nœuds (ex: 500).
*   `START_SCIENTIST` : Point de départ de l'exploration (ex: `"Albert Einstein"`).

## 🏃‍♂️ Utilisation

### Génération du graphe
```bash
python3 main.py
```
*Le script va scanner Wikipédia, interroger l'IA, et construire le graphe en temps réel.*

### Ouvrir la visualisation
Ouvrez simplement le fichier généré dans votre navigateur :
```
output/index.html
```

### Scripts d'analyse avancée

```bash
# Enrichir avec les données temporelles
python3 scripts/enrich_temporal.py

# Détecter les révolutionnaires scientifiques
python3 scripts/paradigm_shifters.py

# Prédire les liens manquants
python3 scripts/link_prediction.py

# Comparer les traditions scientifiques
python3 scripts/tradition_analysis.py

# Valider les relations avec Wikidata
python3 validator.py
```

### Maintenance du graphe

```bash
# Supprimer les nœuds isolés
python3 scripts/remove_isolated.py

# Dédupliquer les nœuds
python3 scripts/deduplicate_nodes.py

# Regrouper les domaines mineurs
python3 scripts/group_to_other.py

# Sauvegarder une version
python3 scripts/save_version.py "v2.0_description"
```

## 📂 Structure du projet

```
.
├── main.py                  # Orchestrateur principal
├── config.py                # Configuration (LLM, limites, etc.)
├── wikipedia_client.py      # Récupération des textes Wikipédia
├── llm_extractor.py         # Extraction des relations via LLM
├── graph_builder.py         # Construction du graphe NetworkX
├── graph_analyzer.py        # PageRank, communautés, métriques
├── visualizer.py            # Génération HTML/JS interactive
├── cache_manager.py         # Cache intelligent pour LLM
├── validator.py             # Validation Wikidata
│
├── scripts/
│   ├── enrich_temporal.py       # Extraction des dates (naissance/mort)
│   ├── paradigm_shifters.py     # Analyse des trous structurels
│   ├── link_prediction.py       # Prédiction de liens manquants
│   ├── tradition_analysis.py    # Comparaison des traditions
│   ├── deduplicate_nodes.py     # Fusion des doublons
│   ├── filter_non_scientists.py # Nettoyage des non-scientifiques
│   ├── remove_isolated.py       # Suppression des nœuds isolés
│   ├── group_to_other.py        # Regroupement des domaines mineurs
│   ├── regenerate_viz.py        # Régénération de la visualisation
│   └── save_version.py          # Sauvegarde avec versioning
│
├── output/
│   ├── index.html           # Visualisation interactive
│   ├── about.html           # Page "À propos" du projet
│   └── scientist_graph.gexf # Graphe au format GEXF (Gephi)
│
├── saves/                   # Versions sauvegardées du graphe
└── data/                    # Cache des réponses LLM
```

## 📊 Métriques du Graphe Actuel

| Métrique | Valeur |
|----------|--------|
| **Nœuds** | ~412 scientifiques |
| **Arêtes** | ~540 relations d'influence |
| **Communautés** | 15 clusters thématiques |
| **Top influenceur** | Isaac Newton (PageRank) |
| **Données temporelles** | 365 scientifiques datés |

## 🛠️ Technologies

*   **Python 3.9+** avec NetworkX, Requests, Wikipedia-API
*   **LLM** : Groq (Llama 3), Ollama, OpenAI, Mistral, Cerebras
*   **Frontend** : vis-network.js, HTML5/CSS3/JavaScript
*   **APIs** : Wikipedia API, Wikidata SPARQL

## 📝 Licence

Projet universitaire - MIASHS L3 - Graphes et Open Data

---

**Auteur** : Terrel Nuentsa  
**Université** : L3 MIASHS - Semestre 2
