"""
Advanced Cross-Reference Validator
===================================
Enhanced validation with multi-source scoring:
- Wikidata SPARQL (doctoral advisor, influence relations)
- Temporal plausibility (chronological verification)
- Wikipedia co-occurrence (mutual citations)
- Confidence scoring with weighted factors
"""

import networkx as nx
import requests
import json
import time
import os
import sys
import re
import hashlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Wikidata SPARQL endpoint
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# Scoring weights
WEIGHTS = {
    "wikidata_doctoral": 0.35,
    "wikidata_influence": 0.25,
    "temporal_plausibility": 0.25,
    "cooccurrence": 0.15,
}

# Minimum confidence to keep a relation
MIN_CONFIDENCE_THRESHOLD = 0.4


class AdvancedValidator:
    """Enhanced validator with multi-source scoring."""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "cache", "validation"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self.request_count = 0
        self.rate_limit_delay = 1.0
        
        # Load graph for temporal data if available
        self.graph = None
        self._load_graph()
    
    def _load_graph(self):
        """Load the graph for temporal data access."""
        gexf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "output", "scientist_graph.gexf"
        )
        if os.path.exists(gexf_path):
            try:
                self.graph = nx.read_gexf(gexf_path)
            except Exception as e:
                print(f"  ⚠️ Could not load graph: {e}")
    
    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _cache_get(self, key: str) -> Optional[dict]:
        path = self._get_cache_path(key)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None
    
    def _cache_set(self, key: str, data: dict):
        path = self._get_cache_path(key)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    # -------------------------------------------------------------------------
    # WIKIDATA METHODS
    # -------------------------------------------------------------------------
    
    def _sparql_query(self, query: str) -> Optional[dict]:
        """Execute a SPARQL query against Wikidata."""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache
        cached = self._cache_get(f"sparql_{query_hash}")
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
                headers={"User-Agent": "ScientistGraphValidator/2.0 (Educational Project)"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self._cache_set(f"sparql_{query_hash}", data)
                return data
            elif response.status_code == 429:
                print(f"  ⚠️ Rate limited, waiting...")
                time.sleep(5)
                return None
            else:
                return None
                
        except Exception as e:
            return None
    
    def find_wikidata_id(self, scientist_name: str) -> Optional[str]:
        """Find the Wikidata Q-ID for a scientist by name."""
        clean_name = scientist_name.replace('"', '\\"')
        
        query = f"""
        SELECT ?item WHERE {{
          ?item wdt:P31 wd:Q5.
          ?item rdfs:label "{clean_name}"@en.
        }}
        LIMIT 1
        """
        
        result = self._sparql_query(query)
        if result and result.get("results", {}).get("bindings"):
            item_uri = result["results"]["bindings"][0]["item"]["value"]
            return item_uri.split("/")[-1]
        
        return None
    
    def check_wikidata_relation(self, source_id: str, target_id: str) -> Dict[str, bool]:
        """Check both doctoral and influence relations in Wikidata."""
        results = {"doctoral": False, "influence": False}
        
        # Doctoral relation (P184: doctoral advisor, P802: doctoral student)
        query_doctoral = f"""
        ASK {{
          {{ wd:{source_id} wdt:P184 wd:{target_id}. }}
          UNION
          {{ wd:{target_id} wdt:P802 wd:{source_id}. }}
          UNION
          {{ wd:{source_id} wdt:P1066 wd:{target_id}. }}
        }}
        """
        
        result = self._sparql_query(query_doctoral)
        results["doctoral"] = result.get("boolean", False) if result else False
        
        # Influence relation (P737: influenced by)
        query_influence = f"""
        ASK {{
          wd:{source_id} wdt:P737 wd:{target_id}.
        }}
        """
        
        result = self._sparql_query(query_influence)
        results["influence"] = result.get("boolean", False) if result else False
        
        return results
    
    # -------------------------------------------------------------------------
    # TEMPORAL PLAUSIBILITY
    # -------------------------------------------------------------------------
    
    def check_temporal_plausibility(self, source_name: str, target_name: str) -> float:
        """
        Check if the influence relation is chronologically possible.
        Returns a score between 0 and 1.
        
        Rules:
        - Target should be born BEFORE source (or same generation)
        - Target should be alive (or have works available) when source was learning
        - Posthumous influence is possible but scored lower
        """
        if not self.graph:
            return 0.5  # Unknown, neutral score
        
        source_data = self.graph.nodes.get(source_name, {})
        target_data = self.graph.nodes.get(target_name, {})
        
        source_birth = source_data.get('birth_year')
        source_death = source_data.get('death_year')
        target_birth = target_data.get('birth_year')
        target_death = target_data.get('death_year')
        
        # Convert to int if string
        try:
            source_birth = int(source_birth) if source_birth else None
            target_birth = int(target_birth) if target_birth else None
            target_death = int(target_death) if target_death else None
        except (ValueError, TypeError):
            return 0.5  # Can't determine, neutral score
        
        if not source_birth or not target_birth:
            return 0.5
        
        # Rule 1: Target should be born before or around the same time as source
        birth_diff = source_birth - target_birth
        
        if birth_diff < -50:
            # Source is 50+ years OLDER than target - impossible influence
            return 0.0
        elif birth_diff < 0:
            # Source is older but less than 50 years - very unlikely
            return 0.2
        elif birth_diff < 20:
            # Same generation (0-20 years) - contemporaries, mutual influence possible
            return 0.7
        elif birth_diff < 50:
            # Target is 20-50 years older - typical mentor/student relationship
            return 1.0
        elif birth_diff < 100:
            # Target is 50-100 years older - posthumous but recent
            return 0.8
        elif birth_diff < 200:
            # Target is 100-200 years older - historical influence
            return 0.6
        else:
            # Target is 200+ years older - ancient influence (less direct)
            return 0.4
    
    # -------------------------------------------------------------------------
    # CO-OCCURRENCE CHECK
    # -------------------------------------------------------------------------
    
    def check_wikipedia_cooccurrence(self, source_name: str, target_name: str) -> float:
        """
        Check if source and target mention each other in their Wikipedia pages.
        This is a proxy for documented relationships.
        Returns score between 0 and 1.
        """
        import wikipediaapi
        
        cache_key = f"cooccur_{hashlib.md5((source_name + target_name).encode()).hexdigest()}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached.get("score", 0.5)
        
        wiki = wikipediaapi.Wikipedia(
            user_agent='ScientistGraphValidator/2.0 (Educational)',
            language='en'
        )
        
        score = 0.0
        
        try:
            # Check if target is mentioned in source's page
            source_page = wiki.page(source_name)
            if source_page.exists():
                if target_name.lower() in source_page.text.lower():
                    score += 0.5
            
            # Check if source is mentioned in target's page
            target_page = wiki.page(target_name)
            if target_page.exists():
                if source_name.lower() in target_page.text.lower():
                    score += 0.5
                    
        except Exception as e:
            score = 0.25  # Partial score if we can't check
        
        self._cache_set(cache_key, {"score": score})
        return score
    
    # -------------------------------------------------------------------------
    # MAIN VALIDATION METHOD
    # -------------------------------------------------------------------------
    
    def validate_and_score(self, source_name: str, target_name: str) -> Dict:
        """
        Full validation with multi-source scoring.
        Returns a detailed result with confidence score.
        """
        result = {
            "source": source_name,
            "target": target_name,
            "scores": {
                "wikidata_doctoral": 0.0,
                "wikidata_influence": 0.0,
                "temporal_plausibility": 0.0,
                "cooccurrence": 0.0,
            },
            "confidence": 0.0,
            "keep": False,
            "evidence": []
        }
        
        # 1. Wikidata validation
        source_id = self.find_wikidata_id(source_name)
        target_id = self.find_wikidata_id(target_name)
        
        if source_id and target_id:
            wikidata_results = self.check_wikidata_relation(source_id, target_id)
            
            if wikidata_results["doctoral"]:
                result["scores"]["wikidata_doctoral"] = 1.0
                result["evidence"].append("Wikidata: doctoral relation confirmed")
            
            if wikidata_results["influence"]:
                result["scores"]["wikidata_influence"] = 1.0
                result["evidence"].append("Wikidata: influence relation confirmed")
        
        # 2. Temporal plausibility
        temporal_score = self.check_temporal_plausibility(source_name, target_name)
        result["scores"]["temporal_plausibility"] = temporal_score
        if temporal_score >= 0.8:
            result["evidence"].append(f"Temporal: chronologically plausible ({temporal_score:.2f})")
        elif temporal_score < 0.3:
            result["evidence"].append(f"Temporal: chronologically suspicious ({temporal_score:.2f})")
        
        # 3. Co-occurrence (only if needed - expensive)
        if result["scores"]["wikidata_doctoral"] == 0 and result["scores"]["wikidata_influence"] == 0:
            cooccur_score = self.check_wikipedia_cooccurrence(source_name, target_name)
            result["scores"]["cooccurrence"] = cooccur_score
            if cooccur_score >= 0.5:
                result["evidence"].append(f"Wikipedia: mutual mentions found ({cooccur_score:.2f})")
        
        # 4. Calculate weighted confidence
        confidence = sum(
            result["scores"][key] * WEIGHTS[key]
            for key in WEIGHTS
        )
        
        result["confidence"] = round(confidence, 3)
        result["keep"] = confidence >= MIN_CONFIDENCE_THRESHOLD
        
        return result


def validate_entire_graph(gexf_path: str, output_path: str = None):
    """
    Validate all edges in the graph and optionally create a filtered version.
    """
    print(f"📂 Loading graph from: {gexf_path}")
    G = nx.read_gexf(gexf_path)
    print(f"   {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    validator = AdvancedValidator()
    
    print(f"\n🔬 Validating all {G.number_of_edges()} relations...")
    print("=" * 70)
    
    results = []
    validated_count = 0
    removed_edges = []
    
    for i, (source, target) in enumerate(G.edges()):
        result = validator.validate_and_score(source, target)
        results.append(result)
        
        status = "✅" if result["keep"] else "❌"
        print(f"  [{i+1}/{G.number_of_edges()}] {status} {source} ← {target} (conf: {result['confidence']:.2f})")
        
        if result["keep"]:
            validated_count += 1
        else:
            removed_edges.append((source, target))
    
    print("\n" + "=" * 70)
    print(f"📊 Validation Summary:")
    print(f"   Total edges: {G.number_of_edges()}")
    print(f"   Validated: {validated_count} ({validated_count/G.number_of_edges()*100:.1f}%)")
    print(f"   To remove: {len(removed_edges)}")
    
    # Create filtered graph if requested
    if output_path:
        G_filtered = G.copy()
        for source, target in removed_edges:
            G_filtered.remove_edge(source, target)
        
        nx.write_gexf(G_filtered, output_path)
        print(f"\n💾 Filtered graph saved to: {output_path}")
        print(f"   New edge count: {G_filtered.number_of_edges()}")
    
    # Save detailed report
    report_path = os.path.join(os.path.dirname(gexf_path), "validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Detailed report saved to: {report_path}")
    
    return results


def main():
    gexf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "scientist_graph.gexf"
    )
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    # Default: validate and show report
    # Optional: pass --filter to create filtered graph
    filter_mode = "--filter" in sys.argv
    
    if filter_mode:
        output_path = gexf_path.replace(".gexf", "_validated.gexf")
        validate_entire_graph(gexf_path, output_path)
    else:
        # Just validate a sample
        print("Running sample validation (first 20 edges)...")
        print("Use --filter flag to validate and filter entire graph.")
        
        G = nx.read_gexf(gexf_path)
        validator = AdvancedValidator()
        
        for source, target in list(G.edges())[:20]:
            result = validator.validate_and_score(source, target)
            status = "✅" if result["keep"] else "❌"
            print(f"{status} {source} ← {target}")
            print(f"   Confidence: {result['confidence']:.2f}")
            for ev in result["evidence"]:
                print(f"   → {ev}")
            print()


if __name__ == "__main__":
    main()
