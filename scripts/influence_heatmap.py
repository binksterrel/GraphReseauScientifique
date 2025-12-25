"""
Influence Epochs Heatmap
========================
Generates a visual heatmap showing which centuries influenced which.
Matrix format: rows = source century, columns = target century

Output: PNG image + interactive HTML version
"""

import networkx as nx
import numpy as np
import os
import sys
import json
from collections import defaultdict

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_graph(gexf_path: str) -> nx.DiGraph:
    """Load the graph from GEXF file."""
    print(f"📂 Loading graph from: {gexf_path}")
    G = nx.read_gexf(gexf_path)
    print(f"   {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def get_century(year: int) -> int:
    """Convert year to century (e.g., 1879 -> 19)."""
    if year is None:
        return None
    return (year - 1) // 100 + 1


def get_century_label(century: int) -> str:
    """Convert century number to readable label."""
    if century <= 0:
        return f"{abs(century)+1}e av. J.-C."
    
    suffixes = {1: "er", 2: "e", 3: "e"}
    suffix = suffixes.get(century, "e")
    return f"{century}{suffix}"


def compute_influence_matrix(G: nx.DiGraph, min_century: int = 15, max_century: int = 21) -> dict:
    """
    Compute influence matrix between centuries.
    
    Returns:
        matrix: numpy array of shape (num_centuries, num_centuries)
        labels: list of century labels
        stats: additional statistics
    """
    num_centuries = max_century - min_century + 1
    matrix = np.zeros((num_centuries, num_centuries))
    
    edges_processed = 0
    edges_skipped = 0
    century_node_counts = defaultdict(int)
    
    for source, target in G.edges():
        source_data = G.nodes.get(source, {})
        target_data = G.nodes.get(target, {})
        
        # Get birth years
        source_birth = source_data.get('birth_year')
        target_birth = target_data.get('birth_year')
        
        # Convert to int
        try:
            source_birth = int(float(source_birth)) if source_birth else None
            target_birth = int(float(target_birth)) if target_birth else None
        except (ValueError, TypeError):
            edges_skipped += 1
            continue
        
        if source_birth is None or target_birth is None:
            edges_skipped += 1
            continue
        
        # Get centuries
        source_century = get_century(source_birth)
        target_century = get_century(target_birth)
        
        # Check bounds
        if not (min_century <= source_century <= max_century) or \
           not (min_century <= target_century <= max_century):
            edges_skipped += 1
            continue
        
        # Relation: source was influenced BY target
        # So target's century is the "source" of influence
        # and source's century is the "recipient"
        row_idx = target_century - min_century  # Influencer
        col_idx = source_century - min_century  # Influenced
        
        matrix[row_idx][col_idx] += 1
        edges_processed += 1
    
    # Count nodes per century
    for node, data in G.nodes(data=True):
        birth = data.get('birth_year')
        try:
            birth = int(float(birth)) if birth else None
        except:
            continue
        if birth:
            century = get_century(birth)
            if min_century <= century <= max_century:
                century_node_counts[century] += 1
    
    labels = [get_century_label(c) for c in range(min_century, max_century + 1)]
    
    stats = {
        "edges_processed": edges_processed,
        "edges_skipped": edges_skipped,
        "total_edges": G.number_of_edges(),
        "nodes_per_century": dict(century_node_counts),
        "max_influence": int(matrix.max()),
        "total_influences": int(matrix.sum()),
    }
    
    return {
        "matrix": matrix,
        "labels": labels,
        "centuries": list(range(min_century, max_century + 1)),
        "stats": stats
    }


def generate_png_heatmap(data: dict, output_path: str):
    """Generate PNG heatmap using matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as colors
    except ImportError:
        print("  ⚠️ matplotlib not installed, skipping PNG generation")
        print("     Install with: pip install matplotlib")
        return
    
    matrix = data["matrix"]
    labels = data["labels"]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Use logarithmic scale for better visualization
    # Add 1 to avoid log(0)
    matrix_log = np.log1p(matrix)
    
    im = ax.imshow(matrix_log, cmap='YlOrRd', aspect='auto')
    
    # Labels
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_yticklabels(labels)
    
    ax.set_xlabel("Siècle influencé (destinataire)", fontsize=12)
    ax.set_ylabel("Siècle influenceur (source)", fontsize=12)
    ax.set_title("Matrice d'Influence Scientifique par Siècle", fontsize=14, fontweight='bold')
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Nombre de relations (échelle log)", rotation=-90, va="bottom")
    
    # Add text annotations
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = int(matrix[i, j])
            if value > 0:
                text = ax.text(j, i, value, ha="center", va="center",
                             color="white" if matrix_log[i, j] > matrix_log.max() / 2 else "black",
                             fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📊 PNG heatmap saved to: {output_path}")


def generate_html_heatmap(data: dict, output_path: str):
    """Generate interactive HTML heatmap."""
    matrix = data["matrix"].tolist()
    labels = data["labels"]
    stats = data["stats"]
    
    # Prepare data for Chart.js or Plotly
    heatmap_data = []
    for i, row_label in enumerate(labels):
        for j, col_label in enumerate(labels):
            value = int(matrix[i][j])
            if value > 0:
                heatmap_data.append({
                    "x": j,
                    "y": i,
                    "v": value,
                    "source": row_label,
                    "target": col_label
                })
    
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heatmap des Influences Scientifiques</title>
    <link rel="icon" type="image/png" href="RSlogo.png">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: #FAFAFA;
            padding: 40px;
            color: #111;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 16px;
            font-weight: 600;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 32px;
            font-size: 1.1rem;
        }}
        #heatmap {{
            width: 100%;
            height: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-top: 32px;
        }}
        .stat-card {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 600;
            color: #000;
        }}
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            margin-top: 4px;
            letter-spacing: 0.05em;
        }}
        .legend {{
            margin-top: 32px;
            padding: 24px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .legend h3 {{
            margin-bottom: 12px;
            font-size: 1rem;
        }}
        .legend p {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <h1>📊 Matrice d'Influence Scientifique par Siècle</h1>
    <p class="subtitle">
        Qui a influencé qui ? Cette heatmap montre les transmissions de savoir entre générations.
    </p>
    
    <div id="heatmap"></div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats['edges_processed']}</div>
            <div class="stat-label">Relations analysées</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['max_influence']}</div>
            <div class="stat-label">Max influences (cellule)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['total_influences']}</div>
            <div class="stat-label">Total influences</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len([c for c, n in stats['nodes_per_century'].items() if n > 0])}</div>
            <div class="stat-label">Siècles couverts</div>
        </div>
    </div>
    
    <div class="legend">
        <h3>📖 Comment lire cette matrice ?</h3>
        <p>
            <strong>Axe Y (vertical)</strong> : Siècle de l'influenceur (source du savoir)<br>
            <strong>Axe X (horizontal)</strong> : Siècle de l'influencé (destinataire)<br><br>
            Exemple : Une cellule [18e, 19e] = 45 signifie que 45 scientifiques du 19e siècle 
            ont été influencés par des scientifiques du 18e siècle.<br><br>
            La diagonale principale montre les influences entre contemporains. 
            Les cellules au-dessus de la diagonale montrent les influences historiques (posthumes).
        </p>
    </div>
    
    <script>
        const z = {json.dumps(matrix)};
        const labels = {json.dumps(labels)};
        
        const trace = {{
            z: z,
            x: labels,
            y: labels,
            type: 'heatmap',
            colorscale: [
                [0, '#FFF5F5'],
                [0.2, '#FEB2B2'],
                [0.4, '#FC8181'],
                [0.6, '#F56565'],
                [0.8, '#E53E3E'],
                [1, '#9B2C2C']
            ],
            hoverongaps: false,
            hovertemplate: '%{{y}} → %{{x}}<br>Relations: %{{z}}<extra></extra>',
            showscale: true,
            colorbar: {{
                title: 'Nombre de relations',
                titleside: 'right'
            }}
        }};
        
        const layout = {{
            xaxis: {{
                title: 'Siècle influencé (destinataire)',
                tickangle: -45
            }},
            yaxis: {{
                title: 'Siècle influenceur (source)',
                autorange: 'reversed'
            }},
            margin: {{ l: 100, r: 50, t: 30, b: 100 }},
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent'
        }};
        
        const config = {{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }};
        
        Plotly.newPlot('heatmap', [trace], layout, config);
    </script>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"  🌐 HTML heatmap saved to: {output_path}")


def main():
    # Default path
    gexf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "scientist_graph.gexf"
    )
    
    if len(sys.argv) > 1:
        gexf_path = sys.argv[1]
    
    G = load_graph(gexf_path)
    
    print("\n📊 Computing influence matrix...")
    data = compute_influence_matrix(G, min_century=15, max_century=21)
    
    print(f"\n📈 Statistics:")
    for key, value in data["stats"].items():
        print(f"   {key}: {value}")
    
    # Output directory
    output_dir = os.path.dirname(gexf_path)
    
    # Generate PNG
    png_path = os.path.join(output_dir, "influence_heatmap.png")
    generate_png_heatmap(data, png_path)
    
    # Generate HTML
    html_path = os.path.join(output_dir, "heatmap.html")
    generate_html_heatmap(data, html_path)
    
    print("\n✅ Heatmap generation complete!")
    print(f"   Open {html_path} in your browser for interactive visualization.")


if __name__ == "__main__":
    main()
