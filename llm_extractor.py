import json
import requests
from typing import Dict, List, Optional, Any
from config import (
    OPENAI_API_KEY,
    USE_OLLAMA,
    OLLAMA_URL,
    OLLAMA_MODEL,
    USE_GROQ,
    GROQ_API_KEY,
    GROQ_MODEL,
    USE_MISTRAL,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    MISTRAL_API_URL,
    USE_CEREBRAS,
    CEREBRAS_API_KEY,
    CEREBRAS_MODEL,
    CEREBRAS_API_URL,
)
from cache_manager import get_cache

class LLMExtractor:
    def __init__(self):
        self.use_ollama = USE_OLLAMA
        self.use_groq = USE_GROQ
        self.use_mistral = USE_MISTRAL
        self.use_cerebras = USE_CEREBRAS
        self.cache = get_cache()  # Initialize cache

        
    def check_connection(self) -> bool:
        """Vérifie si le service LLM configuré est accessible."""
        print("🔍 Vérification du service LLM...")
        
        services = [
            (self.use_cerebras, "Cerebras", CEREBRAS_MODEL, self._check_cerebras),
            (self.use_groq, "Groq", GROQ_MODEL, self._check_groq),
            (self.use_mistral, "Mistral", MISTRAL_MODEL, self._check_mistral),
            (self.use_ollama, "Ollama", OLLAMA_MODEL, self._check_ollama),
        ]

        # Priorité aux services cloud activés, puis Ollama, puis OpenAI
        for enabled, name, model, check_func in services:
            if enabled:
                if check_func(name, model):
                    return True
        
        # Vérification OpenAI (juste présence clé)
        if OPENAI_API_KEY:
             print("  ✅ Mode OpenAI configuré (vérification de clé basique)")
             return True
        
        print("  ❌ Aucun service LLM fonctionnel trouvé.")
        return False

    def _check_groq(self, name: str, model: str) -> bool:
        if not GROQ_API_KEY:
            print(f"  ❌ Clé API {name} manquante")
            return False
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            client.chat.completions.create(messages=[{"role": "user", "content": "Ping"}], model=model)
            print(f"  ✅ Mode {name} configuré et fonctionnel (Modèle: {model})")
            return True
        except Exception as e:
            print(f"  ❌ Erreur de connexion {name}: {e}")
            return False

    def _check_mistral(self, name: str, model: str) -> bool:
        if not MISTRAL_API_KEY:
            print(f"  ❌ Clé API {name} manquante")
            return False
        try:
            resp = requests.get(f"{MISTRAL_API_URL.rstrip('/')}/v1/models", headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"}, timeout=10)
            if resp.status_code == 200:
                print(f"  ✅ Mode {name} configuré et fonctionnel (Modèle: {model})")
                return True
            print(f"  ❌ {name} répond avec erreur {resp.status_code}")
        except Exception as e:
            print(f"  ❌ Erreur de connexion {name}: {e}")
        return False

    def _check_cerebras(self, name: str, model: str) -> bool:
        if not CEREBRAS_API_KEY:
            print(f"  ❌ Clé API {name} manquante")
            return False
        try:
            resp = requests.get(f"{CEREBRAS_API_URL.rstrip('/')}/models", headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}"}, timeout=10)
            if resp.status_code == 200:
                print(f"  ✅ Mode {name} configuré et fonctionnel (Modèle: {model})")
                return True
            print(f"  ❌ {name} répond avec erreur {resp.status_code}")
        except Exception as e:
            print(f"  ❌ Erreur de connexion {name}: {e}")
        return False

    def _check_ollama(self, name: str, model: str) -> bool:
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if resp.status_code == 200:
                print(f"  ✅ Serveur {name} détecté ({OLLAMA_URL})")
                return True
            print(f"  ❌ Serveur {name} répond avec erreur {resp.status_code}")
        except Exception:
            print(f"  ❌ Impossible de se connecter à {name} sur {OLLAMA_URL}")
        return False

    def extract_relations(self, text: str, scientist_name: str, links: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Extrait les relations d'influence depuis un texte Wikipedia.
        Retourne un dictionnaire {'inspirations': [], 'inspired': []}
        """
        links = links or []
        links_hint = ", ".join(links[:200])
        
        # Enhanced Few-Shot + Chain-of-Thought Prompt
        prompt = f"""You are an expert historian of science. Your task is to extract intellectual influence relationships.

## EXAMPLES (Few-Shot Learning)

### Example 1:
Text: "Isaac Newton studied under Isaac Barrow at Cambridge, who introduced him to mathematics."
Analysis:
- Isaac Barrow is explicitly named as Newton's teacher at Cambridge
- This is a documented mentorship relationship
Output: {{"inspirations": ["Isaac Barrow"], "inspired": [], "confidence": "high"}}

### Example 2:
Text: "Einstein's work on special relativity was deeply influenced by Ernst Mach's critique of Newtonian mechanics and Hendrik Lorentz's transformations."
Analysis:
- Ernst Mach's philosophical critique is explicitly credited as an influence
- Lorentz's mathematical work is cited as foundational
- Both are direct intellectual influences, not just contemporaries
Output: {{"inspirations": ["Ernst Mach", "Hendrik Lorentz"], "inspired": [], "confidence": "high"}}

### Example 3:
Text: "Bohr developed his atomic model, which later influenced Heisenberg and Pauli in their quantum mechanics work."
Analysis:
- Heisenberg is named as someone influenced by Bohr's work
- Pauli is also named as influenced
- The influence is on their scientific work specifically
Output: {{"inspirations": [], "inspired": ["Werner Heisenberg", "Wolfgang Pauli"], "confidence": "high"}}

### Example 4:
Text: "Gauss was a contemporary of Laplace and they corresponded occasionally."
Analysis:
- Being a contemporary is NOT an influence relationship
- Occasional correspondence doesn't indicate intellectual influence
- No explicit mentor/student or inspiration relationship
Output: {{"inspirations": [], "inspired": [], "confidence": "medium"}}

## YOUR TASK

Analyze the following text about "{scientist_name}".

Think step by step:
1. Identify all named scientists/philosophers/academics in the text
2. For EACH name, determine if there is EXPLICIT evidence of:
   - Mentorship (teacher/student, doctoral advisor)
   - Intellectual influence (cited as inspiration, built upon their work)
   - NOT just: contemporaries, colleagues, collaborators without influence direction
3. Classify as "inspirations" (influenced {scientist_name}) or "inspired" (influenced BY {scientist_name})
4. Use canonical full names

## CONSTRAINTS
- Return ONLY valid JSON
- Exclude "{scientist_name}" from results
- ONLY include human scientists/academics/philosophers
- EXCLUDE: musicians, artists, writers, politicians, theologians, military figures
- NO institutions, awards, or organizations
- If uncertain about a relationship, omit it
- Prefer precision over recall (fewer false positives)

## HINTS (potential names found in links)
[{links_hint}]

## OUTPUT FORMAT
{{
  "inspirations": ["Full Name 1", "Full Name 2"],
  "inspired": ["Full Name 3"],
  "confidence": "high|medium|low"
}}

## TEXT TO ANALYZE
{text[:25000]}

## YOUR ANALYSIS (Think step by step, then output JSON)
"""
        
        print(f"  🤖 Interrogation du LLM pour {scientist_name}...")
        
        # Check cache first
        cached_result = self.cache.get(text, scientist_name)
        if cached_result is not None:
            print(f"  📦 Résultat trouvé en cache!")
            return cached_result
        
        result = None
        
        # 1. Cerebras
        if self.use_cerebras:
            result = self._call_cerebras(prompt)
        
        # 2. Groq
        if result is None and self.use_groq:
            result = self._call_groq(prompt)

        # 3. Mistral
        if result is None and self.use_mistral:
            result = self._call_mistral(prompt)
            
        # 4. OpenAI
        if result is None and OPENAI_API_KEY:
             result = self._call_openai(prompt)
             
        # 5. Ollama
        if result is None:
            if self.use_cerebras or self.use_groq or self.use_mistral or OPENAI_API_KEY:
                print("  ⚠️ Échec de toutes les APIs cloud -> Tentative locale avec OLLAMA 🦙")
            result = self._call_ollama(prompt)
        
        final_result = result if result else {"inspirations": [], "inspired": []}
        
        # Store in cache
        self.cache.set(text, scientist_name, final_result)
            
        return final_result
    
    def _call_cerebras(self, prompt: str) -> Optional[Dict]:
        """Appel à l'API Cerebras."""
        if not CEREBRAS_API_KEY: return None
        try:
            response = requests.post(
                f"{CEREBRAS_API_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": CEREBRAS_MODEL,
                    "messages": [{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=60,
            )
            if response.status_code != 200:
                print(f"  ⚠️ Erreur Cerebras: {response.status_code}")
                return None
            return self._parse_json_response(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"  ⚠️ Exception Cerebras: {e}")
            return None
            
    def _call_groq(self, prompt: str) -> Optional[Dict]:
        """Appel à l'API Groq."""
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
                model=GROQ_MODEL,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return self._parse_json_response(completion.choices[0].message.content)
        except Exception as e:
            print(f"  ⚠️ Erreur Groq: {e}")
            return None

    def _call_mistral(self, prompt: str) -> Optional[Dict]:
        """Appel à l'API Mistral."""
        if not MISTRAL_API_KEY: return None
        try:
            response = requests.post(
                f"{MISTRAL_API_URL.rstrip('/')}/v1/chat/completions",
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MISTRAL_MODEL,
                    "messages": [{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=60,
            )
            if response.status_code != 200:
                print(f"  ⚠️ Erreur Mistral: {response.status_code}")
                return None
            return self._parse_json_response(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"  ⚠️ Exception Mistral: {e}")
            return None
    
    def _call_ollama(self, prompt: str) -> Optional[Dict]:
        """Appel à Ollama."""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
                timeout=60
            )
            if response.status_code != 200:
                print(f"  ⚠️ Erreur Ollama: {response.status_code}")
                return None
            return self._parse_json_response(response.json().get('response', '{}'))
        except Exception as e:
            print(f"  ⚠️ Exception Ollama: {e}")
            return None
    
    def _call_openai(self, prompt: str) -> Optional[Dict]:
        """Appel à l'API OpenAI (v1.0+)."""
        if not OPENAI_API_KEY: return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return self._parse_json_response(response.choices[0].message.content)
        except ImportError:
             print("  ⚠️ Module 'openai' non trouvé.")
             return None
        except Exception as e:
            print(f"  ⚠️ Erreur OpenAI: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Dict[str, List[str]]:
        """Parse la réponse JSON."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"inspirations": [], "inspired": []}
