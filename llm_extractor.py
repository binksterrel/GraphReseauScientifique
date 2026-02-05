import json
import re
import requests
from typing import Dict, List, Optional

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
from logger import get_logger

logger = get_logger(__name__)


class LLMExtractor:
    def __init__(self) -> None:
        self.use_ollama = USE_OLLAMA
        self.use_groq = USE_GROQ
        self.use_mistral = USE_MISTRAL
        self.use_cerebras = USE_CEREBRAS
        self.cache = get_cache()

    def check_connection(self) -> bool:
        """Vérifie si le service LLM configuré est accessible."""
        logger.info("Verification du service LLM...")

        services = [
            (self.use_cerebras, "Cerebras", CEREBRAS_MODEL, self._check_cerebras),
            (self.use_groq, "Groq", GROQ_MODEL, self._check_groq),
            (self.use_mistral, "Mistral", MISTRAL_MODEL, self._check_mistral),
            (self.use_ollama, "Ollama", OLLAMA_MODEL, self._check_ollama),
        ]

        for enabled, name, model, check_func in services:
            if enabled:
                if check_func(name, model):
                    return True

        if OPENAI_API_KEY:
            logger.info("Mode OpenAI configure (verification de cle basique)")
            return True

        logger.error("Aucun service LLM fonctionnel trouve.")
        return False

    def _check_groq(self, name: str, model: str) -> bool:
        if not GROQ_API_KEY:
            logger.warning(f"Cle API {name} manquante")
            return False
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            client.chat.completions.create(
                messages=[{"role": "user", "content": "Ping"}],
                model=model
            )
            logger.info(f"Mode {name} configure et fonctionnel (Modele: {model})")
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion {name}: {e}")
            return False

    def _check_mistral(self, name: str, model: str) -> bool:
        if not MISTRAL_API_KEY:
            logger.warning(f"Cle API {name} manquante")
            return False
        try:
            resp = requests.get(
                f"{MISTRAL_API_URL.rstrip('/')}/v1/models",
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                timeout=10
            )
            if resp.status_code == 200:
                logger.info(f"Mode {name} configure et fonctionnel (Modele: {model})")
                return True
            logger.error(f"{name} repond avec erreur {resp.status_code}")
        except Exception as e:
            logger.error(f"Erreur de connexion {name}: {e}")
        return False

    def _check_cerebras(self, name: str, model: str) -> bool:
        if not CEREBRAS_API_KEY:
            logger.warning(f"Cle API {name} manquante")
            return False
        try:
            resp = requests.get(
                f"{CEREBRAS_API_URL.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}"},
                timeout=10
            )
            if resp.status_code == 200:
                logger.info(f"Mode {name} configure et fonctionnel (Modele: {model})")
                return True
            logger.error(f"{name} repond avec erreur {resp.status_code}")
        except Exception as e:
            logger.error(f"Erreur de connexion {name}: {e}")
        return False

    def _check_ollama(self, name: str, model: str) -> bool:
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if resp.status_code == 200:
                logger.info(f"Serveur {name} detecte ({OLLAMA_URL})")
                return True
            logger.error(f"Serveur {name} repond avec erreur {resp.status_code}")
        except Exception:
            logger.error(f"Impossible de se connecter a {name} sur {OLLAMA_URL}")
        return False

    def extract_relations(
        self,
        text: str,
        scientist_name: str,
        links: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Extrait les relations d'influence depuis un texte Wikipedia.
        Retourne un dictionnaire {'inspired_by': [], 'inspired': []}
        """
        links = links or []

        prompt = f"""You are a world expert in the history of science.

TASK: Analyze the provided text about scientist "{scientist_name}" and extract their intellectual network.
You must identify:
1. "inspired_by": Mentors, teachers, and scientists who influenced {scientist_name}.
2. "inspired": Students, successors, and scientists influenced by {scientist_name}.

### CRITICAL RULES:
- OUTPUT MUST BE VALID JSON.
- USE "Firstname Lastname" format (No surname alone).
- JSON keys MUST be exactly "inspired_by" and "inspired".
- Do not invent information. Only extract what is implied in the text.

## TEXT TO ANALYZE:
{text[:15000]}

### FINAL INSTRUCTION:
Return ONLY the JSON object.
Format:
{{
  "inspired_by": ["List of names"],
  "inspired": ["List of names"]
}}
"""

        logger.debug(f"Interrogation du LLM pour {scientist_name}...")

        # Check cache first
        cached_result = self.cache.get(text, scientist_name)
        if cached_result is not None:
            logger.debug(f"Resultat trouve en cache pour {scientist_name}")
            return cached_result

        result: Optional[Dict[str, List[str]]] = None

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
                logger.warning("Echec de toutes les APIs cloud -> Tentative locale avec OLLAMA")
            result = self._call_ollama(prompt)

        final_result = result if result else {"inspired_by": [], "inspired": []}

        # Store in cache
        self.cache.set(text, scientist_name, final_result)

        return final_result

    def _call_cerebras(self, prompt: str) -> Optional[Dict[str, List[str]]]:
        """Appel à l'API Cerebras."""
        if not CEREBRAS_API_KEY:
            return None
        try:
            response = requests.post(
                f"{CEREBRAS_API_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {CEREBRAS_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": CEREBRAS_MODEL,
                    "messages": [
                        {"role": "system", "content": "JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.warning(f"Erreur Cerebras: {response.status_code}")
                return None

            return self._parse_json_response(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"Exception Cerebras: {e}")
            return None

    def _call_groq(self, prompt: str) -> Optional[Dict[str, List[str]]]:
        """Appel à l'API Groq."""
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=GROQ_MODEL,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return self._parse_json_response(completion.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Erreur Groq: {e}")
            return None

    def _call_mistral(self, prompt: str) -> Optional[Dict[str, List[str]]]:
        """Appel à l'API Mistral."""
        if not MISTRAL_API_KEY:
            return None
        try:
            response = requests.post(
                f"{MISTRAL_API_URL.rstrip('/')}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MISTRAL_MODEL,
                    "messages": [
                        {"role": "system", "content": "JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.warning(f"Erreur Mistral: {response.status_code}")
                return None
            return self._parse_json_response(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"Exception Mistral: {e}")
            return None

    def _call_ollama(self, prompt: str) -> Optional[Dict[str, List[str]]]:
        """Appel à Ollama."""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                    "format": "json"
                },
                timeout=120
            )
            if response.status_code != 200:
                logger.warning(f"Erreur Ollama: {response.status_code}")
                return None

            return self._parse_json_response(response.json().get('response', '{}'))
        except Exception as e:
            logger.warning(f"Exception Ollama: {e}")
            return None

    def _call_openai(self, prompt: str) -> Optional[Dict[str, List[str]]]:
        """Appel à l'API OpenAI (v1.0+)."""
        if not OPENAI_API_KEY:
            return None
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
            logger.warning("Module 'openai' non trouve.")
            return None
        except Exception as e:
            logger.warning(f"Erreur OpenAI: {e}")
            return None

    def _parse_json_response(self, response: str) -> Dict[str, List[str]]:
        """
        Parse la réponse JSON avec plusieurs stratégies de fallback.
        """
        default: Dict[str, List[str]] = {"inspired_by": [], "inspired": []}

        if not response:
            return default

        # Tentative 1: JSON direct
        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return {
                    "inspired_by": result.get("inspired_by", []),
                    "inspired": result.get("inspired", [])
                }
        except json.JSONDecodeError:
            pass

        # Tentative 2: Extraction entre accolades
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end > start:
                extracted = response[start:end + 1]
                result = json.loads(extracted)
                if isinstance(result, dict):
                    return {
                        "inspired_by": result.get("inspired_by", []),
                        "inspired": result.get("inspired", [])
                    }
        except json.JSONDecodeError:
            pass

        # Tentative 3: Extraction via regex
        try:
            inspired_by: List[str] = []
            inspired: List[str] = []

            # Chercher les listes dans le texte
            inspired_by_match = re.search(
                r'"inspired_by"\s*:\s*\[(.*?)\]',
                response,
                re.DOTALL
            )
            if inspired_by_match:
                names = re.findall(r'"([^"]+)"', inspired_by_match.group(1))
                inspired_by = [n for n in names if len(n) > 2]

            inspired_match = re.search(
                r'"inspired"\s*:\s*\[(.*?)\]',
                response,
                re.DOTALL
            )
            if inspired_match:
                names = re.findall(r'"([^"]+)"', inspired_match.group(1))
                inspired = [n for n in names if len(n) > 2]

            if inspired_by or inspired:
                return {"inspired_by": inspired_by, "inspired": inspired}
        except Exception:
            pass

        logger.debug("Echec du parsing JSON, retour valeur par defaut")
        return default
