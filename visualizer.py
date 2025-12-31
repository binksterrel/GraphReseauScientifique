from pyvis.network import Network
import networkx as nx
import os

class GraphVisualizer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        
    def create_interactive_html(self, output_file: str = "output/graph.html", alt_graph=None):
        """
        Génère une visualisation interactive minimaliste et épurée.
        """
        if self.graph.number_of_nodes() == 0:
            print("⚠️ Graphe vide, pas de visualisation.")
            return

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Calculer le PageRank pour la taille des nœuds
        try:
            pagerank = nx.pagerank(self.graph)
        except Exception:
            # Fallback: utiliser le degré normalisé pour avoir des tailles variées
            pagerank = nx.degree_centrality(self.graph)

        # Vérifier si le graphe a des attributs de domaine scientifique
        has_field_data = any(self.graph.nodes[n].get('field') for n in self.graph.nodes())
        
        if has_field_data:
            # Groupement par Domaine Scientifique
            field_communities = {}
            community_map = {}
            
            for node in self.graph.nodes():
                field = self.graph.nodes[node].get('field', 'Other')
                if field not in field_communities:
                    field_communities[field] = []
                field_communities[field].append(node)
                community_map[node] = field
            
            communities = list(field_communities.values())
            
            field_colors = {
                'Physics': '#2563EB',
                'Mathematics': '#7C3AED',
                'Chemistry': '#059669',
                'Biology': '#65A30D',
                'Computer Science': '#0891B2',
                'Medicine': '#DC2626',
                'Astronomy': '#4B5563',
                'Engineering': '#EA580C',
                'Philosophy': '#DB2777',
                'Economics': '#D97706',
                'Other': '#9CA3AF'
            }
            use_field_colors = True
        else:
            # Fallback: Détection de communautés par graphe
            try:
                communities = sorted(nx.community.greedy_modularity_communities(self.graph.to_undirected()), key=len, reverse=True)
                community_map = {}
                for i, comm in enumerate(communities):
                    for node in comm:
                        community_map[node] = i
            except Exception:
                community_map = {n: 0 for n in self.graph.nodes()}
                communities = [list(self.graph.nodes())]
            
            # Palette de couleurs pour les communautés
            community_colors = [
                "#1F2937", "#4B5563", "#9CA3AF", "#DC2626", "#EA580C",
                "#D97706", "#65A30D", "#059669", "#0891B2", "#2563EB",
                "#7C3AED", "#DB2777"
            ]
            use_field_colors = False

        # Fonction pour nettoyer les noms (retirer les parenthèses de désambiguïsation)
        def clean_name(name):
            if "(" in name:
                return name.split("(")[0].strip()
            return name

        # Légende basée sur le type de groupement
        legend_data = []
        if use_field_colors:
            for field, nodes_list in field_communities.items():
                if field and len(nodes_list) > 0:
                    legend_data.append({
                        "label": f"{field} ({len(nodes_list)})",
                        "color": field_colors.get(field, '#9CA3AF')
                    })
        else:
            for i, comm in enumerate(communities):
                if i >= len(community_colors): break
                leader = max(comm, key=lambda n: pagerank.get(n, 0))
                leader_clean = clean_name(leader)
                legend_data.append({
                    "label": f"Cercle de {leader_clean}",
                    "color": community_colors[i]
                })

        # Préparation des données pour Vis.js
        nodes_data = []
        for node in self.graph.nodes():
            score = pagerank.get(node, 0)
            size = 8 + min(score * 80, 35)  # Taille compacte pour lisibilité
            
            # Couleur basée sur le type de groupement
            if use_field_colors:
                field = community_map.get(node, 'Other')
                color = field_colors.get(field, '#9CA3AF')
            else:
                comm_id = community_map.get(node, 0)
                color = community_colors[comm_id % len(community_colors)]
            
            # Label nettoyé pour l'affichage
            label_display = clean_name(node)
            
            nodes_data.append({
                "id": node,
                "label": label_display,
                "title": f"{label_display}",
                "size": size,
                "color": color,
                "borderWidth": 1,
                "borderWidthSelected": 2,
                "shape": "dot",
                "font": {"color": "#0A0A0A", "face": "Inter", "size": 11}
            })
            
        edges_data = []
        for idx, (u, v, data) in enumerate(self.graph.edges(data=True)):
            edges_data.append({
                "id": f"e{idx}",
                "from": u,
                "to": v,
                "title": "A influencé",
                "color": {"color": "#E5E5E5", "highlight": "#0A0A0A", "hover": "#0A0A0A"},
                "width": 0.5,
                "arrows": {"to": {"enabled": True, "scaleFactor": 0.3}},
                "hoverWidth": 0.5 
            })


            
        import json
        json_nodes = json.dumps(nodes_data)
        json_edges = json.dumps(edges_data)

        json_legend = json.dumps(legend_data)
        total_nodes = len(nodes_data)
        
        # Calculer les Hubs (Degree Centrality - Top 5%)
        try:
            degree = nx.degree_centrality(self.graph)
            sorted_degree = sorted(degree.items(), key=lambda x: x[1], reverse=True)
            top_count = max(10, int(len(sorted_degree) * 0.05))
            hubs = [n for n, _ in sorted_degree[:top_count]]
            json_hubs = json.dumps(hubs)
            json_hubs_count = len(hubs)
        except:
            json_hubs = "[]"
            json_hubs_count = 0
        
        if '\0' in json_edges:
            json_edges = json_edges.replace('\0', '')
        
        # Calculer les passeurs de savoir (Betweenness Centrality - Top 5%)
        try:
            betweenness = nx.betweenness_centrality(self.graph)
            sorted_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
            # Garder le top 5% (ou minimum 10)
            top_count = max(10, int(len(sorted_betweenness) * 0.05))
            passeurs = [n for n, _ in sorted_betweenness[:top_count]]
            json_passeurs = json.dumps(passeurs)
            json_passeurs_count = len(passeurs)
        except:
            json_passeurs = "[]"
            json_passeurs_count = 0
        
        # Split f-string to avoid potential issues with large json_edges injection
        html_head = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#FFFFFF">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <title>RÉSEAU SCIENTIFIQUE</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #FAFAFA;
            color: #0A0A0A;
            overflow: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        /* Icons */
        .icon-sm {{
            width: 14px;
            height: 14px;
            vertical-align: middle;
        }}
        
        .icon-md {{
            width: 18px;
            height: 18px;
            vertical-align: middle;
        }}
        
        @keyframes spin {{ 
            from {{ transform: rotate(0deg); }} 
            to {{ transform: rotate(360deg); }} 
        }}
        
        .spin {{
            animation: spin 1s linear infinite;
        }}

        #mynetwork {{
            width: 100%;
            height: 100%;
            outline: none;
            padding-bottom: 48px; /* Space for status bar */
        }}
        
        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 32px 48px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
            pointer-events: none;
        }}
        
        .logo {{
            font-size: 15px;
            font-weight: 500;
            letter-spacing: -0.02em;
            color: #0A0A0A;
            pointer-events: all;
        }}
        
        .stats {{
            font-size: 13px;
            color: #6A6A6A;
            font-weight: 400;
            pointer-events: all;
        }}
        
        /* Animated Background */
        /* Animated Background (Aurora) */
        .aurora-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -2;
            background: #FAFAFA;
            overflow: hidden;
        }}

        .orb {{
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.6;
            animation: float 20s infinite ease-in-out;
        }}

        .orb-1 {{
            width: 60vw;
            height: 60vw;
            background: #E0E7FF;
            top: -20%;
            left: -10%;
            animation-delay: 0s;
        }}

        .orb-2 {{
            width: 50vw;
            height: 50vw;
            background: #F0FDFA;
            bottom: -10%;
            right: -10%;
            animation-delay: -5s;
        }}

        .orb-3 {{
            width: 40vw;
            height: 40vw;
            background: #F5F3FF;
            top: 40%;
            left: 40%;
            animation-delay: -10s;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) scale(1); }}
            33% {{ transform: translate(30px, -50px) scale(1.1); }}
            66% {{ transform: translate(-20px, 20px) scale(0.95); }}
        }}

        /* Noise Texture */
        .noise-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            opacity: 0.03;
            pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }}

        .sidebar {{
            position: fixed;
            top: 50%;
            left: 24px;
            transform: translateY(-50%); /* Base state */
            width: 300px;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            z-index: 100;
            border: 1px solid rgba(0, 0, 0, 0.05);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            opacity: 0;
            animation: slideInCenter 0.6s ease forwards 0.3s;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
        }}

        @keyframes slideInCenter {{
            from {{ opacity: 0; transform: translate(0, -40%); }}
            to {{ opacity: 1; transform: translate(0, -50%); }}
        }}
        
        @keyframes slideIn {{
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .search-box {{
            width: 100%;
            padding: 10px 14px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            font-size: 13px;
            font-family: 'Inter', sans-serif;
            background: rgba(255, 255, 255, 0.5);
            transition: all 0.2s ease;
            outline: none;
        }}
        
        .search-box:focus {{
            border-color: #0A0A0A;
            background: #FFFFFF;
        }}
        
        .search-box::placeholder {{
            color: #9A9A9A;
        }}
        
        .info-panel {{
            margin-top: 20px;
            font-size: 13px;
            color: #6A6A6A;
            min-height: 60px;
        }}
        
        .node-name {{
            font-size: 16px;
            font-weight: 500;
            color: #0A0A0A;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }}
        
        .node-score {{
            font-size: 12px;
            color: #9A9A9A;
            margin-bottom: 16px;
        }}
        
        .legend {{
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid rgba(0, 0, 0, 0.06);
        }}
        
        .legend-title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #9CA3AF;
            margin-bottom: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 12px;
            color: #6A6A6A;
        }}
        
        .legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        
        /* --- NEW MINIMALIST LOADING SCREEN --- */
        .loading {{
            position: fixed;
            inset: 0;
            background: #FFFFFF;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            transition: opacity 1s cubic-bezier(0.23, 1, 0.32, 1);
        }}
        
        .loading-content {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 24px;
            opacity: 0;
            animation: fadeInSlow 1.2s ease forwards;
        }}

        @keyframes fadeInSlow {{
            from {{ opacity: 0; transform: scale(0.98); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        
        .loading-title {{
            font-size: 14px;
            font-weight: 500;
            color: #111827;
            letter-spacing: 0.2em;
            text-transform: uppercase;
        }}
        
        .progress-container {{
            width: 120px;
            height: 1px;
            background: rgba(0,0,0,0.06);
            position: relative;
            overflow: hidden;
        }}
        
        .progress-bar {{
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 0%;
            background: #000000;
            transition: width 0.4s ease;
        }}
        
        .loading-status {{
            margin-top: 12px;
            font-size: 12px;
            color: #9CA3AF;
            font-family: monospace;
        }}
        /* ------------------------------------- */

        /* --- STATUS BAR (REPLACES TOASTS) --- */
        .status-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 48px;
            background: #FFFFFF;
            border-top: 1px solid rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            padding: 0 48px;
            font-size: 13px;
            color: #333;
            z-index: 1000;
            gap: 12px;
        }}
        
        .status-separator {{
            width: 1px;
            height: 16px;
            background: #E5E5E5;
        }}
        
        .search-results {{
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            right: 0;
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
            display: none;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }}
        
        .search-results.active {{
            display: block;
        }}
        
        .search-result-item {{
            padding: 10px 14px;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.15s ease;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
        }}
        
        .search-result-item:last-child {{
            border-bottom: none;
        }}
        
        .search-result-item:hover {{
            background: #FAFAFA;
        }}
        
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 0;
            margin-right: 16px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
            background: transparent;
            text-decoration: none;
        }}

        .btn-wiki {{
            color: #4B5563;
            border-bottom: 1px solid transparent;
        }}
        
        .btn-wiki:hover {{
            color: #111827;
            border-bottom-color: #111827;
        }}

        .btn-delete {{
            color: #9CA3AF;
        }}
        
        .btn-delete:hover {{
            color: #EF4444;
        }}
        
        .floating-actions {{
            position: fixed;
            bottom: 80px;
            right: 48px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 100;
        }}
        
        .filter-control {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: white;
            padding: 8px 12px;
            border-radius: 12px;
            border: 1px solid rgba(0,0,0,0.1);
            box-shadow: 0 8px 16px rgba(0,0,0,0.06);
            font-size: 12px;
            color: #27272A;
        }}
        
        .filter-control input[type="range"] {{
            width: 100px;
            cursor: pointer;
        }}
        
        .filter-control span {{
            min-width: 35px;
            text-align: right;
            font-weight: 500;
        }}

        .btn-floating {{
            width: 44px;
            height: 44px;
            background: white;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.06);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.2s ease;
            color: #27272A;
        }}

        .btn-floating:hover, .btn-floating.active {{
            transform: translateY(-2px);
            box-shadow: 0 12px 20px rgba(0,0,0,0.08);
            border-color: #0A0A0A;
            color: #0A0A0A;
        }}
        
        .btn-floating.active {{
            background: #18181B;
            color: white;
            border-color: #18181B;
        }}
        
    </style>
</head>
<body>
    
    <div id="app-header"></div>
    
    <!-- Aurora Background -->
    <div class="aurora-container">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    </div>
    <div class="noise-overlay"></div>

    <div class="sidebar">
        <div style="position: relative;">
            <input type="text" id="search-input" class="search-box" placeholder="Rechercher...">
            <div id="search-results" class="search-results"></div>
        </div>
        
        <div id="info-panel" class="info-panel">
            Sélectionnez un nœud pour voir les détails
        </div>
        
        <div class="legend">
            <div class="legend-title">Communautés Détectées</div>
            <div id="legend-content">
                <!-- Généré dynamiquement -->
            </div>
        </div>
    </div>

    <div id="mynetwork"></div>
    
    <div id="loading" class="loading">
        <div class="loading-content">
            <div class="loading-title">RÉSEAU SCIENTIFIQUE</div>
            <div class="progress-container">
                <div id="progress-bar" class="progress-bar"></div>
            </div>
            <div id="loading-status" class="loading-status">0%</div>
        </div>
    </div>
    
    <div class="floating-actions">
        <div class="filter-control" title="Nombre de scientifiques affichés">
            <i data-lucide="users" class="icon-sm"></i>
            <input type="range" id="node-filter" min="10" max="{total_nodes}" value="{total_nodes}" oninput="filterNodes(this.value)">
            <span id="filter-count">{total_nodes}</span>
        </div>
        
        <div style="display: flex; gap: 12px;">
            <button onclick="toggleHubs()" id="btn-hubs" class="btn-floating" title="Hubs (Top 5% les plus connectés)">
                <i data-lucide="star" class="icon-md"></i>
            </button>
            <button onclick="togglePasseurs()" id="btn-passeurs" class="btn-floating" title="Passeurs de Savoir (Top 5%)">
                <i data-lucide="link" class="icon-md"></i>
            </button>
            <button onclick="togglePathMode()" id="btn-path" class="btn-floating" title="Trouver un itinéraire">
                <i data-lucide="map-pin" class="icon-md"></i>
            </button>
            <button onclick="resetView()" class="btn-floating" title="Recentrer la vue">
                <i data-lucide="maximize" class="icon-md"></i>
            </button>
        </div>
    </div>
    
    <div id="status-bar" class="status-bar">
        <span id="status-icon"><i data-lucide="activity" class="icon-sm"></i></span>
        <span id="status-text">Prêt</span>
        <span class="status-separator" style="width: 1px; height: 12px; background: rgba(0,0,0,0.1); margin: 0 8px;"></span>
        <span class="stats">
            <span id="node-count">0</span> nœuds · <span id="edge-count">0</span> liens
        </span>
        

    </div>

    <script type="text/javascript">
        const nodesData = {json_nodes};
        const edgesData = """
        
        html_middle = json_edges
        
        html_tail = f""";
        const legendData = {json_legend};
        const hubs = new Set({json_hubs});
        const hubsCount = {json_hubs_count};
        const passeurs = new Set({json_passeurs});
        const passeursCount = {json_passeurs_count};
        
        // Générer la légende dynamiquement basée sur les données (sans "Other")
        const legendContent = document.getElementById('legend-content');
        legendData.filter(item => !item.label.startsWith('Other')).forEach(item => {{
            const div = document.createElement('div');
            div.className = 'legend-item';
            div.innerHTML = `<span class="legend-dot" style="background: ${{item.color}};"></span><span>${{item.label}}</span>`;
            legendContent.appendChild(div);
        }});


        document.getElementById('node-count').innerText = nodesData.length;
        document.getElementById('edge-count').innerText = edgesData.length;

        const container = document.getElementById('mynetwork');
        
        // Variables globales pour le filtrage
        const nodes = new vis.DataSet(nodesData);
        const edges = new vis.DataSet(edgesData);
        const allNodesData = [...nodesData]; // Keep original copy
        const allEdgesData = [...edgesData];
        
        
        const data = {{
            nodes: nodes,
            edges: edges
        }};
        
        const options = {{
            nodes: {{
                shape: 'dot',
                font: {{ 
                    size: 11, 
                    color: '#0A0A0A',
                    face: 'Inter'
                }}, 
                borderWidth: 1
            }},
            edges: {{
                width: 0.5,
                color: {{ color: '#E5E5E5', highlight: '#0A0A0A', hover: '#0A0A0A' }},
                smooth: {{ 
                    type: 'continuous',
                    roundness: 0.5
                }},
                selectionWidth: 2,
                hoverWidth: 0.5
            }},
            physics: {{
                stabilization: {{ 
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 25
                }},
                barnesHut: {{
                    gravitationalConstant: -2000,
                    centralGravity: 0.2,
                    springLength: 120,
                    springConstant: 0.02,
                    damping: 0.15,
                    avoidOverlap: 0.1
                }}
            }},
            interaction: {{ 
                hover: true, 
                tooltipDelay: 300,
                zoomView: true,
                dragView: true,
                navigationButtons: false
            }}
        }};

        const network = new vis.Network(container, data, options);
        
        // --- LOADING SYSTEM ---
        const loader = document.getElementById('loading');
        const progressBar = document.getElementById('progress-bar');
        const statusText = document.getElementById('loading-status');
        
        network.on("stabilizationProgress", function(params) {{
            const widthFactor = params.iterations / params.total;
            const width = Math.round(widthFactor * 100);
            progressBar.style.width = width + '%';
            statusText.innerText = `Optimisation physique ${{width}}%`;
        }});

        network.once("stabilizationIterationsDone", function() {{
            progressBar.style.width = '100%';
            statusText.innerText = '100%';
            
            // Démarrage immersif : zoom sur le premier scientifique
            if(nodesData.length > 0) {{
                const centralNode = nodesData[0].id;
                network.focus(centralNode, {{
                    scale: 1.8,
                    animation: {{
                        duration: 1200,
                        easingFunction: "easeInOutQuad"
                    }}
                }});
            }}
            
            setTimeout(() => {{
                loader.style.opacity = '0';
                loader.style.pointerEvents = 'none';
                setTimeout(() => loader.remove(), 1000);
            }}, 500);
        }});
        
        // Fallback safety if stabilization is too fast or disabled
        setTimeout(() => {{
             const loader = document.getElementById('loading');
             if(loader && loader.parentElement) {{
                 loader.style.opacity = '0';
                 setTimeout(() => loader.remove(), 1000);
             }}
        }}, 6000);

        const searchInput = document.getElementById('search-input');
        const resultsBox = document.getElementById('search-results');
        
        searchInput.addEventListener('input', (e) => {{
            const val = e.target.value.toLowerCase();
            if(val.length < 2) {{ 
                resultsBox.classList.remove('active'); 
                return; 
            }}
            
            const matches = nodesData.filter(n => n.label.toLowerCase().includes(val));
            resultsBox.innerHTML = '';
            
            if(matches.length > 0) {{
                resultsBox.classList.add('active');
                matches.forEach(node => {{
                    const div = document.createElement('div');
                    div.className = "search-result-item";
                    div.innerText = node.label;
                    div.onclick = () => {{
                        focusNode(node.id);
                        resultsBox.classList.remove('active');
                        searchInput.value = '';
                    }};
                    resultsBox.appendChild(div);
                }});
            }} else {{
                resultsBox.classList.remove('active');
            }}
        }});
        
        // Initial Icons
        lucide.createIcons();

        // --- STATUS BAR LOGIC ---
        function updateStatus(htmlContent) {{
            const sb = document.getElementById('status-bar');
            sb.innerHTML = htmlContent;
            lucide.createIcons();
        }}

        // --- PATHFINDING LOGIC ---
        let pathMode = false;
        let pathStartNode = null;
        let pathEdges = [];
        let animationOffset = 0;
        
        function togglePathMode() {{
            pathMode = !pathMode;
            pathStartNode = null;
            pathEdges = [];
            stopMarchingAnts();
            
            const btn = document.getElementById('btn-path');
            if(pathMode) {{
                btn.classList.add('active');
                updateStatus('<i data-lucide="map-pin" class="icon-sm"></i> <b>Mode Itinéraire</b> : Sélectionnez le point de départ sur le graphe');
                network.unselectAll();
            }} else {{
                btn.classList.remove('active');
                updateStatus('<i data-lucide="activity" class="icon-sm"></i> Prêt');
                // Reset edge colors
                const allEdges = data.edges.getIds();
                const updates = allEdges.map(id => ({{id: id, color: {{ color: '#E5E5E5', highlight: '#0A0A0A' }}, width: 0.5, dashes: false}}));
                data.edges.update(updates);
                network.redraw();
            }}
        }}

        let marchingAntsInterval = null;
        
        function startMarchingAnts(edges) {{
            // Masquer l'arête statique (opacity 0) pour ne voir que l'animation canvas par dessus
            const updates = edges.map(id => ({{id: id, color: {{opacity: 0}}}}));
            data.edges.update(updates);
            
            pathEdges = edges;
            network.on("afterDrawing", drawPathAnimation);
            
            // Lancer la boucle d'animation
            animatePath();
        }}
        
        function animatePath() {{
            if (pathEdges.length > 0) {{
                network.redraw(); // Force le redraw pour appeler afterDrawing
                requestAnimationFrame(animatePath);
            }}
        }}
        
        function stopMarchingAnts() {{
            network.off("afterDrawing", drawPathAnimation);
            pathEdges = [];
            // La boucle s'arrêtera car pathEdges est vide
        }}

        function drawPathAnimation(ctx) {{
            if (pathEdges.length === 0) return;
            animationOffset = (animationOffset - 0.5);
            ctx.save();
            ctx.beginPath();
            ctx.strokeStyle = '#2563EB';
            ctx.lineWidth = 4;
            ctx.setLineDash([10, 15]);
            ctx.lineDashOffset = animationOffset;
            
            pathEdges.forEach(edgeId => {{
                const edge = data.edges.get(edgeId);
                const node1 = network.body.nodes[edge.from];
                const node2 = network.body.nodes[edge.to];
                if (node1 && node2) {{
                    ctx.moveTo(node1.x, node1.y);
                    ctx.lineTo(node2.x, node2.y);
                }}
            }});
            ctx.stroke();
            ctx.restore();
        }}

        function findPath(start, end) {{
            let queue = [[start]];
            let visited = new Set();
            visited.add(start);
            
            while (queue.length > 0) {{
                let path = queue.shift();
                let node = path[path.length - 1];
                if (node === end) return path;
                const connectedNodes = network.getConnectedNodes(node); 
                for (let neighbor of connectedNodes) {{
                    if (!visited.has(neighbor)) {{
                        visited.add(neighbor);
                        let newPath = [...path, neighbor];
                        queue.push(newPath);
                    }}
                }}
            }}
            return null;
        }}
        
        function highlightPath(path) {{
            const allEdges = data.edges.getIds();
            const resetUpdates = allEdges.map(id => ({{id: id, color: {{ color: '#E5E5E5', opacity: 0.1 }}, width: 0.5, dashes: false}}));
            data.edges.update(resetUpdates);
            stopMarchingAnts();
            const edgesToAnimate = [];
            for (let i = 0; i < path.length - 1; i++) {{
                const u = path[i];
                const v = path[i+1];
                const edgeObj = data.edges.get().find(e => 
                    (e.from === u && e.to === v) || (e.from === v && e.to === u)
                );
                if (edgeObj) edgesToAnimate.push(edgeObj.id);
            }}
            startMarchingAnts(edgesToAnimate);
            updateStatus(`<i data-lucide="check-circle" class="icon-sm"></i> <b>Itinéraire trouvé</b> : ${{path.length - 1}} liens de connexion`);
        }}

        function focusNode(nodeId) {{
            network.selectNodes([nodeId]);
            network.focus(nodeId, {{
                scale: 1.5,
                animation: {{ duration: 800, easingFunction: "easeInOutCubic" }}
            }});
            showNodeDetails(nodeId);
        }}

        network.on("click", function (params) {{
            if (pathMode) {{
                if (params.nodes.length > 0) {{
                    const clickedNode = params.nodes[0];
                    if (!pathStartNode) {{
                        pathStartNode = clickedNode;
                        updateStatus(`<i data-lucide="flag" class="icon-sm"></i> <b>Départ : ${{cleanName(clickedNode)}}</b>. Maintenant, cliquez sur la destination.`);
                    }} else {{
                        const pathEndNode = clickedNode;
                        if (pathStartNode === pathEndNode) return;
                        
                        updateStatus(`<i data-lucide="loader-2" class="icon-sm spin"></i> Calcul de l'itinéraire en cours...`);
                        const path = findPath(pathStartNode, pathEndNode);
                        
                        if (path) {{
                            highlightPath(path);
                        }} else {{
                            updateStatus(`<i data-lucide="x-circle" class="icon-sm"></i> <b>Erreur</b> : Aucun chemin trouvé entre ces deux points.`);
                            pathStartNode = null;
                        }}
                    }}
                }}
                return;
            }}
            
            if (params.nodes.length > 0) {{
                showNodeDetails(params.nodes[0]);
            }} else if (params.edges.length > 0) {{
                const edgeId = params.edges[0];
                const edge = data.edges.get(edgeId);
                showEdgeDetails(edge);
            }} else {{
                resetInfoPanel();
            }}
        }});
        
        function cleanName(name) {{
            if (name.includes('(')) return name.split('(')[0].trim();
            return name;
        }}
        
        function showEdgeDetails(edge) {{
            const panel = document.getElementById('info-panel');
            const fromLabel = cleanName(edge.from);
            const toLabel = cleanName(edge.to);
            panel.innerHTML = `
                <div class="node-name" style="font-size: 15px;">Relation d'Influence</div>
                <div class="node-score" style="color: #6A6A6A; margin-bottom: 8px;">
                     <span style="font-weight:600; color:#18181B;">${{fromLabel}}</span>
                     <div style="display:flex;justify-content:center;margin:4px 0;"><i data-lucide="arrow-down" class="icon-sm"></i></div>
                     <span style="font-weight:600; color:#18181B;">${{toLabel}}</span>
                </div>
            `;
            lucide.createIcons();
        }}

        function showNodeDetails(nodeId) {{
            const node = data.nodes.get(nodeId);
            const panel = document.getElementById('info-panel');
            const score = (node.size / 600).toFixed(4);
            const connectedNodes = network.getConnectedNodes(nodeId);
            const wikiUrl = "https://en.wikipedia.org/wiki/" + encodeURIComponent(node.id);
            panel.innerHTML = `
                <div class="node-name">${{node.label}}</div>
                <div class="node-score">
                    Indice d'Influence : ${{score}} 
                    <span onclick="showScoreInfo()" style="cursor:pointer; margin-left:4px;" title="Plus d'info"><i data-lucide="info" class="icon-sm" style="color:#A1A1AA;"></i></span>
                </div>
                <div class="node-score" style="margin-bottom: 16px;">Connexions : ${{connectedNodes.length}}</div>
                <div style="display:flex; align-items:center; margin-top:8px;">
                    <a href="${{wikiUrl}}" target="_blank" class="btn btn-wiki">Lien Wikipédia</a>
                    <button onclick="deleteNode('${{nodeId}}')" class="btn btn-delete">Supprimer</button>
                </div>
            `;
            lucide.createIcons();
        }}
        
        function deleteNode(nodeId) {{
            if(!confirm("Supprimer " + nodeId + " et ses connexions ?")) return;
            const connectedEdges = network.getConnectedEdges(nodeId);
            const count = connectedEdges.length;
            data.nodes.remove({{id: nodeId}});
            const newNodes = data.nodes.length;
            const newEdges = data.edges.length; 
            document.getElementById('node-count').innerText = newNodes;
            document.getElementById('edge-count').innerText = newEdges;
            
            // Status bar update instead of toast
            updateStatus(`<b>${{nodeId}}</b> supprimé. ${{count}} liens ont été retirés.`);
            
            resetInfoPanel();
            network.unselectAll();
            lucide.createIcons();
        }}
        
        function showScoreInfo() {{
            // Status bar update instead of toast
            updateStatus("<b>Indice d'Influence (PageRank)</b> : Mesure l'importance d'un scientifique selon ses connexions.");
            lucide.createIcons();
        }}
        
        function resetInfoPanel() {{
            document.getElementById('info-panel').innerHTML = 'Sélectionnez un nœud pour voir les détails';
        }}
        
        // Filtre dynamique des nœuds par importance
        const sortedBySize = [...nodesData].sort((a, b) => b.size - a.size);
        // allNodesData and allEdgesData already declared above
        


        // Fonction pour mettre à jour la légende avec les comptes dynamiques
        function updateLegend(visibleNodes) {{
            const fieldCounts = {{}};
            visibleNodes.forEach(n => {{
                // Trouver le domaine du noeud via legendData
                const legendItem = legendData.find(item => item.color === n.color);
                const field = legendItem ? legendItem.label.split(' (')[0] : 'Other';
                fieldCounts[field] = (fieldCounts[field] || 0) + 1;
            }});
            
            // Mettre à jour la légende
            const legendContent = document.getElementById('legend-content');
            legendContent.innerHTML = '';
            
            // Trier par nombre décroissant et exclure "Other"
            const sortedFields = Object.entries(fieldCounts)
                .filter(([field]) => field !== 'Other')
                .sort((a, b) => b[1] - a[1]);
            sortedFields.forEach(([field, count]) => {{
                const item = legendData.find(l => l.label.startsWith(field));
                const color = item ? item.color : '#CCCCCC';
                const div = document.createElement('div');
                div.className = 'legend-item';
                div.innerHTML = `<span class="legend-dot" style="background: ${{color}};"></span><span>${{field}} (${{count}})</span>`;
                legendContent.appendChild(div);
            }});
        }}
        
        function filterNodes(count) {{
            console.log('filterNodes appelé avec:', count);
            count = parseInt(count);
            document.getElementById('filter-count').textContent = count;
            
            // Obtenir les top N nœuds par taille (PageRank)
            const topNodes = sortedBySize.slice(0, count);
            const topNodeIds = new Set(topNodes.map(n => n.id));
            
            // Filtrer les arêtes pour ne garder que celles entre les nœuds visibles
            const filteredEdges = allEdgesData.filter(e => 
                topNodeIds.has(e.from) && topNodeIds.has(e.to)
            );
            
            // Effacer et recréer les données
            nodes.clear();
            edges.clear();
            nodes.add(topNodes);
            edges.add(filteredEdges);
            
            // Mise à jour du compteur
            document.getElementById('node-count').textContent = count;
            document.getElementById('edge-count').textContent = filteredEdges.length;
            
            // Mise à jour de la légende
            updateLegend(topNodes);
            
            updateStatus(`Affichage de ${{count}} scientifiques`);
        }}
        
        // Hubs (Top 5% Degree Centrality)
        let hubsActive = false;
        const originalColors = {{}};
        
        function toggleHubs() {{
            const btn = document.getElementById('btn-hubs');
            hubsActive = !hubsActive;
            
            // Obtenir les nœuds actuellement visibles
            const currentNodes = nodes.get();
            
            if (hubsActive) {{
                btn.classList.add('active');
                const hubsInView = currentNodes.filter(n => hubs.has(n.id)).length;
                updateStatus(`⭐ Hubs: ${{hubsInView}}/${{hubsCount}} visibles (Top 5% connectés)`);
                
                // Sauvegarder les couleurs originales et appliquer mise en évidence
                const updates = [];
                currentNodes.forEach(n => {{
                    if (!originalColors[n.id]) originalColors[n.id] = n.color;
                    if (hubs.has(n.id)) {{
                        updates.push({{ id: n.id, color: '#FFD700', borderWidth: 3 }});
                    }} else {{
                        updates.push({{ id: n.id, color: '#E5E5E5', borderWidth: 1 }});
                    }}
                }});
                nodes.update(updates);
            }} else {{
                btn.classList.remove('active');
                updateStatus('Vue normale');
                
                // Restaurer les couleurs originales
                const updates = [];
                currentNodes.forEach(n => {{
                    updates.push({{ id: n.id, color: originalColors[n.id] || n.color, borderWidth: 1 }});
                }});
                nodes.update(updates);
            }}
            lucide.createIcons();
        }}
        
        // Passeurs de Savoir (Betweenness Centrality - Top 5%)
        let passeursActive = false;
        
        function togglePasseurs() {{
            const btn = document.getElementById('btn-passeurs');
            passeursActive = !passeursActive;
            
            // Obtenir les nœuds actuellement visibles
            const currentNodes = nodes.get();
            
            if (passeursActive) {{
                btn.classList.add('active');
                const passeursInView = currentNodes.filter(n => passeurs.has(n.id)).length;
                updateStatus(`🔗 Passeurs: ${{passeursInView}}/${{passeursCount}} visibles (Top 5% Intermédiarité)`);
                
                // Mettre en évidence les passeurs
                const updates = [];
                currentNodes.forEach(n => {{
                    if (!originalColors[n.id]) originalColors[n.id] = n.color;
                    if (passeurs.has(n.id)) {{
                        updates.push({{ id: n.id, color: '#00D9FF', borderWidth: 3 }});
                    }} else {{
                        updates.push({{ id: n.id, color: '#E5E5E5', borderWidth: 1 }});
                    }}
                }});
                nodes.update(updates);
            }} else {{
                btn.classList.remove('active');
                updateStatus('Vue normale');
                
                // Restaurer les couleurs originales
                const updates = [];
                currentNodes.forEach(n => {{
                    updates.push({{ id: n.id, color: originalColors[n.id] || n.color, borderWidth: 1 }});
                }});
                nodes.update(updates);
            }}
            lucide.createIcons();
        }}
        
        function resetView() {{
            network.fit({{ animation: {{ duration: 1000, easingFunction: "easeInOutQuart" }} }});
        }}
    </script>
    <script src="header.js"></script>
</body>
</html>"""
        
        html_content = html_head + html_middle + html_tail
        
        print(f"✨ Génération de la visualisation minimaliste (FR)...")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"   Fichier créé: {output_file}")
        except Exception as e:
            print(f"⚠️ Erreur: {e}")
