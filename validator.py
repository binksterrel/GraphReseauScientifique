"""
Cross-Reference Validator
=========================
Validates extracted influence relations against external sources:
- Wikidata SPARQL (P184: doctoral advisor, P802: student)
- Provides confidence scoring based on source count
"""

import requests
import json
import time
import os
import sys
from typing import Optional, Dict, List, Tuple

# Wikidata SPARQL endpoint
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# Property IDs for relationships
WIKIDATA_PROPERTIES = {
    "doctoral_advisor": "P184",
    "doctoral_student": "P802",
    "influenced_by": "P737",
    "student_of": "P1066",
    "teacher": "P1066",  # Alias
}

class WikidataValidator:
    """Validates relations against Wikidata."""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "wikidata")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.request_count = 0
        self.rate_limit_delay = 1.0  # seconds between requests
    
    def _get_cache_path(self, query_hash: str) -> str:
        return os.path.join(self.cache_dir, f"{query_hash}.json")
    
    def _cache_get(self, query_hash: str) -> Optional[dict]:
        path = self._get_cache_path(query_hash)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None
    
    def _cache_set(self, query_hash: str, data: dict):
        path = self._get_cache_path(query_hash)
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def _sparql_query(self, query: str) -> Optional[dict]:
        """Execute a SPARQL query against Wikidata."""
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache
        cached = self._cache_get(query_hash)
        if cached:
            return cached
        
        # Rate limiting
        self.request_count += 1
        if self.request_count > 1:
            time.sleep(self.rate_limit_delay)
        
        try:
            response = requests.get(
                WIKIDATA_ENDPOINT,
                params={"query": query, "format": "json"},
                headers={"User-Agent": "ScientistGraphValidator/1.0 (Educational Project)"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self._cache_set(query_hash, data)
                return data
            else:
                print(f"  ⚠️ Wikidata error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ⚠️ Wikidata request failed: {e}")
            return None
    
    def find_wikidata_id(self, scientist_name: str) -> Optional[str]:
        """Find the Wikidata Q-ID for a scientist by name."""
        # Clean name for search
        clean_name = scientist_name.replace('"', '\\"')
        
        query = f"""
        SELECT ?item ?itemLabel WHERE {{
          ?item wdt:P31 wd:Q5.  # Instance of human
          ?item rdfs:label "{clean_name}"@en.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        
        result = self._sparql_query(query)
        if result and result.get("results", {}).get("bindings"):
            item_uri = result["results"]["bindings"][0]["item"]["value"]
            # Extract Q-ID from URI
            return item_uri.split("/")[-1]
        
        # Try fuzzy search
        query_fuzzy = f"""
        SELECT ?item ?itemLabel WHERE {{
          ?item wdt:P31 wd:Q5.
          ?item rdfs:label ?label.
          FILTER(CONTAINS(LCASE(?label), LCASE("{clean_name}")))
          FILTER(LANG(?label) = "en")
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        
        result = self._sparql_query(query_fuzzy)
        if result and result.get("results", {}).get("bindings"):
            item_uri = result["results"]["bindings"][0]["item"]["value"]
            return item_uri.split("/")[-1]
        
        return None
    
    def check_doctoral_relation(self, source_id: str, target_id: str) -> bool:
        """Check if there's a doctoral advisor/student relation in Wikidata."""
        query = f"""
        ASK {{
          {{ wd:{source_id} wdt:P184 wd:{target_id}. }}  # source's advisor is target
          UNION
          {{ wd:{target_id} wdt:P802 wd:{source_id}. }}  # target's student is source
        }}
        """
        
        result = self._sparql_query(query)
        return result.get("boolean", False) if result else False
    
    def check_influence_relation(self, source_id: str, target_id: str) -> bool:
        """Check if there's an influence relation in Wikidata (P737)."""
        query = f"""
        ASK {{
          wd:{source_id} wdt:P737 wd:{target_id}.  # source was influenced by target
        }}
        """
        
        result = self._sparql_query(query)
        return result.get("boolean", False) if result else False
    
    def validate_relation(self, source_name: str, target_name: str) -> Dict:
        """
        Validate a relation between two scientists.
        Returns confidence score and evidence.
        """
        print(f"  🔍 Validating: {source_name} ← {target_name}")
        
        evidence = {
            "wikidata_doctoral": False,
            "wikidata_influence": False,
            "source_found": False,
            "target_found": False,
        }
        
        # Find Wikidata IDs
        source_id = self.find_wikidata_id(source_name)
        target_id = self.find_wikidata_id(target_name)
        
        evidence["source_found"] = source_id is not None
        evidence["target_found"] = target_id is not None
        
        if source_id and target_id:
            # Check doctoral relation
            evidence["wikidata_doctoral"] = self.check_doctoral_relation(source_id, target_id)
            
            # Check influence relation
            evidence["wikidata_influence"] = self.check_influence_relation(source_id, target_id)
        
        # Calculate confidence
        score = 0.0
        if evidence["wikidata_doctoral"]:
            score += 0.5
        if evidence["wikidata_influence"]:
            score += 0.3
        if evidence["source_found"] and evidence["target_found"]:
            score += 0.1  # Both exist in Wikidata
        
        # No external validation found but both exist
        if score == 0.1:
            score = 0.2  # Low confidence, relation might exist
        
        return {
            "source": source_name,
            "target": target_name,
            "confidence": score,
            "evidence": evidence,
            "validated": score >= 0.5
        }


def validate_graph_sample(gexf_path: str, sample_size: int = 20):
    """Validate a sample of relations from the graph."""
    import networkx as nx
    
    print(f"📂 Loading graph from: {gexf_path}")
    G = nx.read_gexf(gexf_path)
    
    # Get sample of edges
    edges = list(G.edges())[:sample_size]
    
    validator = WikidataValidator()
    
    print(f"\n🔬 Validating {len(edges)} relations against Wikidata...")
    print("=" * 60)
    
    results = []
    validated_count = 0
    
    for source, target in edges:
        result = validator.validate_relation(source, target)
        results.append(result)
        
        if result["validated"]:
            validated_count += 1
            print(f"  ✅ {source} ← {target} (confidence: {result['confidence']:.2f})")
        else:
            print(f"  ⚠️ {source} ← {target} (confidence: {result['confidence']:.2f})")
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Summary:")
    print(f"   Checked: {len(edges)}")
    print(f"   Validated: {validated_count} ({validated_count/len(edges)*100:.1f}%)")
    print(f"   Unvalidated: {len(edges) - validated_count}")


if __name__ == "__main__":
    gexf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "scientist_graph.gexf")
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    validate_graph_sample(gexf_path, sample_size=15)
