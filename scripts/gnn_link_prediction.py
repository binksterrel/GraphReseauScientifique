"""
GNN Link Prediction
===================
Predicts missing influence relationships using Graph Neural Networks.
Uses node embeddings learned from the graph structure to identify
potential connections that may not be documented.

Two implementations:
1. Full GNN (PyTorch Geometric) - if available
2. Fallback (Node2Vec + sklearn) - always works
"""

import networkx as nx
import numpy as np
import os
import sys
import json
from typing import List, Tuple, Dict
from collections import defaultdict

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_graph(gexf_path: str) -> nx.DiGraph:
    """Load the graph from GEXF file."""
    print(f"📂 Loading graph from: {gexf_path}")
    G = nx.read_gexf(gexf_path)
    print(f"   {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def check_pytorch_geometric() -> bool:
    """Check if PyTorch Geometric is available."""
    try:
        import torch
        import torch_geometric
        return True
    except ImportError:
        return False


# =============================================================================
# FALLBACK IMPLEMENTATION: Node2Vec + Random Forest
# =============================================================================

def create_node_features(G: nx.Graph) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Create feature vectors for each node based on graph properties.
    Features: [degree, pagerank, clustering, in_degree, out_degree, field_encoded]
    """
    # Node to index mapping
    node_to_idx = {node: i for i, node in enumerate(G.nodes())}
    
    # Compute metrics
    undirected = G.to_undirected()
    
    degree = dict(G.degree())
    in_degree = dict(G.in_degree()) if G.is_directed() else degree
    out_degree = dict(G.out_degree()) if G.is_directed() else degree
    
    try:
        pagerank = nx.pagerank(G)
    except:
        pagerank = {n: 1.0/len(G) for n in G.nodes()}
    
    try:
        clustering = nx.clustering(undirected)
    except:
        clustering = {n: 0.0 for n in G.nodes()}
    
    # Encode fields
    fields = set()
    for node in G.nodes():
        field = G.nodes[node].get('field', 'Unknown')
        fields.add(field)
    field_to_idx = {f: i for i, f in enumerate(sorted(fields))}
    
    # Build feature matrix
    n_nodes = len(G.nodes())
    n_features = 5 + len(fields)  # 5 numeric + one-hot encoded fields
    
    features = np.zeros((n_nodes, n_features))
    
    for node in G.nodes():
        idx = node_to_idx[node]
        
        # Normalize numeric features
        features[idx, 0] = degree[node] / max(degree.values()) if degree.values() else 0
        features[idx, 1] = pagerank[node]
        features[idx, 2] = clustering[node]
        features[idx, 3] = in_degree[node] / max(in_degree.values()) if in_degree.values() else 0
        features[idx, 4] = out_degree[node] / max(out_degree.values()) if out_degree.values() else 0
        
        # One-hot encode field
        field = G.nodes[node].get('field', 'Unknown')
        field_idx = field_to_idx.get(field, 0)
        features[idx, 5 + field_idx] = 1.0
    
    return features, node_to_idx


def generate_edge_features(features: np.ndarray, node_to_idx: Dict[str, int],
                          source: str, target: str) -> np.ndarray:
    """Generate features for a potential edge (source, target)."""
    if source not in node_to_idx or target not in node_to_idx:
        return None
    
    src_feat = features[node_to_idx[source]]
    tgt_feat = features[node_to_idx[target]]
    
    # Combine features: concatenation + element-wise operations
    edge_feat = np.concatenate([
        src_feat,
        tgt_feat,
        src_feat * tgt_feat,  # Hadamard product
        np.abs(src_feat - tgt_feat),  # Absolute difference
    ])
    
    return edge_feat


def train_link_predictor_fallback(G: nx.DiGraph, train_ratio: float = 0.8):
    """
    Train a Random Forest classifier on existing edges.
    Uses negative sampling for non-edges.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score, precision_score, recall_score
    
    print("\n🔧 Training link predictor (Random Forest fallback)...")
    
    # Create node features
    features, node_to_idx = create_node_features(G)
    
    # Positive samples: existing edges
    positive_edges = list(G.edges())
    
    # Negative samples: random non-edges (same size as positive)
    nodes = list(G.nodes())
    existing = set(G.edges())
    negative_edges = []
    
    np.random.seed(42)
    attempts = 0
    while len(negative_edges) < len(positive_edges) and attempts < len(positive_edges) * 10:
        src = np.random.choice(nodes)
        tgt = np.random.choice(nodes)
        if src != tgt and (src, tgt) not in existing and (tgt, src) not in existing:
            negative_edges.append((src, tgt))
        attempts += 1
    
    print(f"   Positive samples: {len(positive_edges)}")
    print(f"   Negative samples: {len(negative_edges)}")
    
    # Generate features for all edges
    X = []
    y = []
    
    for src, tgt in positive_edges:
        feat = generate_edge_features(features, node_to_idx, src, tgt)
        if feat is not None:
            X.append(feat)
            y.append(1)
    
    for src, tgt in negative_edges:
        feat = generate_edge_features(features, node_to_idx, src, tgt)
        if feat is not None:
            X.append(feat)
            y.append(0)
    
    X = np.array(X)
    y = np.array(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1-train_ratio, random_state=42)
    
    # Train Random Forest
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred_proba = clf.predict_proba(X_test)[:, 1]
    y_pred = clf.predict(X_test)
    
    auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    
    print(f"\n📊 Model Performance:")
    print(f"   AUC-ROC: {auc:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    
    return clf, features, node_to_idx


def predict_missing_links(G: nx.DiGraph, clf, features: np.ndarray, 
                         node_to_idx: Dict[str, int], top_k: int = 50) -> List[Dict]:
    """
    Predict the most likely missing links.
    """
    print(f"\n🔮 Predicting top {top_k} missing links...")
    
    nodes = list(G.nodes())
    existing = set(G.edges())
    
    predictions = []
    
    # Sample pairs to check (checking all is O(n²))
    pairs_to_check = []
    
    # Strategy: Focus on pairs with common neighbors
    for node in nodes:
        neighbors = set(G.predecessors(node)) | set(G.successors(node))
        for neighbor in neighbors:
            second_hop = set(G.predecessors(neighbor)) | set(G.successors(neighbor))
            for candidate in second_hop:
                if candidate != node and (node, candidate) not in existing and (candidate, node) not in existing:
                    pairs_to_check.append((node, candidate))
    
    # Remove duplicates
    pairs_to_check = list(set(pairs_to_check))
    print(f"   Checking {len(pairs_to_check)} candidate pairs...")
    
    # Predict
    for src, tgt in pairs_to_check:
        feat = generate_edge_features(features, node_to_idx, src, tgt)
        if feat is not None:
            proba = clf.predict_proba(feat.reshape(1, -1))[0, 1]
            
            predictions.append({
                "source": src,
                "target": tgt,
                "probability": float(proba),
                "source_field": G.nodes[src].get('field', 'Unknown'),
                "target_field": G.nodes[tgt].get('field', 'Unknown'),
            })
    
    # Sort by probability
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    
    return predictions[:top_k]


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Default path
    gexf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "scientist_graph.gexf"
    )
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    G = load_graph(gexf_path)
    
    # Check if PyTorch Geometric is available
    if check_pytorch_geometric():
        print("✅ PyTorch Geometric detected - using GNN model")
        # TODO: Full GNN implementation
        print("   (GNN implementation in progress, using fallback for now)")
    else:
        print("ℹ️ PyTorch Geometric not found - using Random Forest fallback")
        print("   Install with: pip install torch torch-geometric")
    
    # Train model
    try:
        clf, features, node_to_idx = train_link_predictor_fallback(G)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install with: pip install scikit-learn")
        return
    
    # Predict missing links
    predictions = predict_missing_links(G, clf, features, node_to_idx, top_k=50)
    
    # Display results
    print("\n" + "=" * 80)
    print("🔮 TOP 30 PREDICTED MISSING LINKS")
    print("=" * 80)
    print("These relationships are not documented but are statistically likely.\n")
    
    for i, pred in enumerate(predictions[:30], 1):
        src = pred["source"]
        tgt = pred["target"]
        prob = pred["probability"]
        src_field = pred["source_field"]
        tgt_field = pred["target_field"]
        
        print(f"{i:2}. {src} ← {tgt}")
        print(f"    Probability: {prob:.2%}")
        print(f"    Fields: {src_field} ← {tgt_field}")
        print()
    
    # Save results
    output_dir = os.path.dirname(gexf_path)
    output_path = os.path.join(output_dir, "predicted_links.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Full predictions saved to: {output_path}")
    
    # Generate HTML report
    html_path = os.path.join(output_dir, "predicted_links.html")
    generate_html_report(predictions, html_path)
    print(f"🌐 HTML report saved to: {html_path}")


def generate_html_report(predictions: List[Dict], output_path: str):
    """Generate an HTML report of predicted links."""
    
    rows = ""
    for i, pred in enumerate(predictions[:50], 1):
        prob_pct = pred["probability"] * 100
        color = "#22c55e" if prob_pct > 70 else "#eab308" if prob_pct > 50 else "#64748b"
        
        rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{pred['source']}</strong></td>
            <td>←</td>
            <td><strong>{pred['target']}</strong></td>
            <td style="color: {color}; font-weight: 600;">{prob_pct:.1f}%</td>
            <td><span class="field-pill">{pred['source_field']}</span></td>
            <td><span class="field-pill">{pred['target_field']}</span></td>
        </tr>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Prédictions de Liens Manquants</title>
    <link rel="icon" type="image/png" href="RSlogo.png">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #FAFAFA; padding: 40px; color: #111; }}
        h1 {{ font-size: 2rem; margin-bottom: 8px; }}
        .subtitle {{ color: #666; margin-bottom: 32px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
        th {{ background: #111; color: white; padding: 16px; text-align: left; font-weight: 600; }}
        td {{ padding: 12px 16px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        .field-pill {{ background: rgba(0,0,0,0.05); padding: 4px 10px; border-radius: 100px; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>🔮 Prédictions de Liens Manquants</h1>
    <p class="subtitle">Relations d'influence probables non documentées, identifiées par Machine Learning.</p>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Influencé</th>
                <th></th>
                <th>Influenceur</th>
                <th>Probabilité</th>
                <th>Domaine 1</th>
                <th>Domaine 2</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == "__main__":
    main()
