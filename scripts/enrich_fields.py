import networkx as nx
import os
import sys
import time
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OLLAMA_URL, OLLAMA_MODEL

def call_ollama_simple(prompt):
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"Ollama Error: {e}")
    return None

def enrich_fields(input_file, output_file):
    print(f"Loading graph from {input_file}...")
    try:
        g = nx.read_gexf(input_file)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    nodes_to_process = [n for n, d in g.nodes(data=True) if not d.get('field') or d.get('field') == 'Unknown']
    total = len(nodes_to_process)
    print(f"Found {total} nodes with missing or 'Unknown' field.")
    
    if total == 0:
        print("Nothing to do.")
        return

    processed = 0
    errors = 0

    print("Using Ollama directly for simple field extraction...")

    for node_id in nodes_to_process:
        print(f"[{processed+1}/{total}] Enriching: {node_id}...")
        
        prompt = f"""
        Identify the ONE primary scientific field for: "{node_id}".
        Options: Physics, Mathematics, Philosophy, Astronomy, Chemistry, Biology, Computer Science, Literature.
        If multiple apply, pick the most famous one.
        If strictly unknown person, return "Unknown".
        Output ONLY the single word. No punctuation.
        """
        
        field = call_ollama_simple(prompt)
        
        if field:
            # Cleanup
            field = field.strip().replace('"', '').replace('.', '')
            if len(field) > 20: 
                # Fallback clean if model chatters
                field = field.split('\n')[0].split(' ')[0]
            
            # Normalize common variations
            if "mathematic" in field.lower(): field = "Mathematics"
            if "physic" in field.lower(): field = "Physics"
            if "philosophy" in field.lower() or "philosopher" in field.lower(): field = "Philosophy"
            
            print(f"   -> Found: {field}")
            g.nodes[node_id]['field'] = field
        else:
            print("   -> Failed to get response.")
            errors += 1
            
        processed += 1
        
        # Save periodically
        if processed % 10 == 0:
            print(f"Saving progress to {output_file}...")
            nx.write_gexf(g, output_file)

    print(f"Finished. Saving final result to {output_file}...")
    nx.write_gexf(g, output_file)
    print(f"Done. Processed: {processed}, Errors: {errors}")

if __name__ == "__main__":
    gexf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "scientist_graph.gexf")
    enrich_fields(gexf_path, gexf_path)
