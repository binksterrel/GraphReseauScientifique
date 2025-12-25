# 🔴 LIVE GRAPH GENERATION

Ce document explique comment utiliser la fonctionnalité de génération en temps réel.

## 📋 Prérequis

Installez la dépendance supplémentaire pour le serveur WebSocket :

```bash
pip install flask flask-socketio flask-cors python-socketio
```

## 🚀 Lancement du Serveur

1. **Démarrer le serveur backend** :
   ```bash
   python3 server.py
   ```
   
   Le serveur démarre sur `http://localhost:5050`

2. **Ouvrir la page Live** :
   ```
   http://localhost:5050/live.html
   ```
   
   Ou directement ouvrir : `output/live.html`

## 🎬 Utilisation

1. **Cliquez sur "Lancer une exploration"**
2. **Entrez le scientifique de départ** (ex: "Albert Einstein")
3. **Définissez le nombre maximum de nœuds** (ex: 50)
4. **Observez la génération en temps réel !**

## 📊 Interface

La page affiche en temps réel :
- ✅ **Connexion au serveur** (vert)
- 🔵 **Nouveaux nœuds** avec leur domaine scientifique
- 🟣 **Nouvelles arêtes** entre scientifiques
- 📈 **Progression** (tous les 10 nœuds)
- 💾 **Checkpoints** automatiques (tous les 10 nœuds)
- ❌ **Erreurs** LLM/réseau

## ⚙️ Configuration

Modifiez `config.py` pour ajuster :
- `MAX_DEPTH` : Profondeur d'exploration
- LLM utilisé (Groq, OpenAI, Mistral, etc.)

## 🛑 Arrêt

- **Fermer le navigateur** : La génération continue en arrière-plan
- **Arrêter le serveur** : `Ctrl+C` dans le terminal

## 📝 Notes

- Les checkpoints sont sauvegardés dans `output/scientist_graph.gexf`
- La visualisation finale est générée dans `output/graph.html`
- Le serveur utilise le port **5050** (modifiable dans `server.py`)

## 🐛 Résolution de Problèmes

### "Erreur de connexion"
→ Vérifiez que `python3 server.py` est lancé

### "Port 5050 already in use"
→ Tuez le processus : `lsof -ti:5050 | xargs kill -9`

### "LLM introuvable"
→ Configurez une clé API dans `config.py`
