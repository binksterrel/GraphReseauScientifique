#!/usr/bin/env python3
"""
Analyse Small-World et Power Law du graphe Episteme Network.

Vérifie si le graphe présente les propriétés d'un réseau petit monde
(Watts-Strogatz) et d'un réseau scale-free (Barabási-Albert).

Génère un rapport HTML interactif avec graphiques.

Usage: python3 scripts/small_world_analysis.py
"""

import os
import sys
import json
import random
import math
from collections import Counter

import networkx as nx
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_graph(path: str = "output/scientist_graph.gexf") -> nx.DiGraph:
    if not os.path.exists(path):
        print(f"Fichier introuvable : {path}")
        sys.exit(1)
    return nx.read_gexf(path)


def small_world_analysis(G_undirected: nx.Graph) -> dict:
    """
    Compare le graphe réel avec un graphe aléatoire Erdős-Rényi
    de même taille pour vérifier les propriétés Small-World.
    """
    n = G_undirected.number_of_nodes()
    m = G_undirected.number_of_edges()
    p = (2 * m) / (n * (n - 1)) if n > 1 else 0

    print("\n  Calcul du coefficient de clustering moyen...")
    C_real = nx.average_clustering(G_undirected)

    print("  Calcul de la longueur moyenne des plus courts chemins...")
    # Sur la plus grande composante connexe
    largest_cc = max(nx.connected_components(G_undirected), key=len)
    G_cc = G_undirected.subgraph(largest_cc).copy()
    L_real = nx.average_shortest_path_length(G_cc)

    print("  Génération du graphe aléatoire Erdős-Rényi pour comparaison...")
    # Moyenne sur 5 graphes aléatoires pour robustesse
    C_randoms = []
    L_randoms = []
    for i in range(5):
        G_rand = nx.erdos_renyi_graph(n, p, seed=42 + i)
        C_randoms.append(nx.average_clustering(G_rand))
        # Plus grande composante connexe du graphe aléatoire
        if G_rand.number_of_edges() > 0:
            largest_rand = max(nx.connected_components(G_rand), key=len)
            G_rand_cc = G_rand.subgraph(largest_rand).copy()
            if G_rand_cc.number_of_nodes() > 1:
                L_randoms.append(nx.average_shortest_path_length(G_rand_cc))

    C_random = np.mean(C_randoms) if C_randoms else 0
    L_random = np.mean(L_randoms) if L_randoms else 0

    # Coefficient sigma de Small-World (Humphries & Gurney, 2008)
    # sigma = (C_real / C_random) / (L_real / L_random)
    # sigma >> 1 → réseau petit monde
    sigma = 0
    if C_random > 0 and L_random > 0:
        sigma = (C_real / C_random) / (L_real / L_random)

    is_small_world = sigma > 1.0

    return {
        "n": n,
        "m": m,
        "density": p,
        "clustering_real": round(C_real, 4),
        "clustering_random": round(C_random, 4),
        "clustering_ratio": round(C_real / C_random, 2) if C_random > 0 else 0,
        "path_length_real": round(L_real, 2),
        "path_length_random": round(L_random, 2),
        "path_length_ratio": round(L_real / L_random, 2) if L_random > 0 else 0,
        "sigma": round(sigma, 2),
        "is_small_world": is_small_world,
        "largest_cc_size": len(largest_cc),
        "diameter": nx.diameter(G_cc),
    }


def degree_distribution_analysis(G: nx.Graph) -> dict:
    """
    Analyse la distribution des degrés pour vérifier
    si le graphe suit une loi de puissance (scale-free).
    """
    degrees = [d for _, d in G.degree()]
    degree_count = Counter(degrees)

    # Préparer les données pour le plot log-log
    ks = sorted(degree_count.keys())
    pks = [degree_count[k] / len(degrees) for k in ks]

    # Filtrer les zéros pour le log
    log_data = [(k, pk) for k, pk in zip(ks, pks) if k > 0 and pk > 0]
    log_ks = [math.log10(k) for k, _ in log_data]
    log_pks = [math.log10(pk) for _, pk in log_data]

    # Régression linéaire sur le log-log pour estimer l'exposant gamma
    # P(k) ~ k^(-gamma)  =>  log(P(k)) = -gamma * log(k) + C
    gamma = 0.0
    r_squared = 0.0
    intercept = 0.0
    if len(log_ks) > 2:
        x = np.array(log_ks)
        y = np.array(log_pks)
        A = np.vstack([x, np.ones(len(x))]).T
        result = np.linalg.lstsq(A, y, rcond=None)
        slope, intercept = result[0]
        gamma = -slope

        # R² pour mesurer la qualité de l'ajustement
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Typiquement gamma entre 2 et 3 pour un réseau scale-free
    is_scale_free = 1.5 < gamma < 4.0 and r_squared > 0.6

    # Statistiques descriptives
    avg_degree = np.mean(degrees)
    max_degree = max(degrees)
    median_degree = np.median(degrees)

    # Top 10 hubs
    degree_dict = dict(G.degree())
    top_hubs = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "avg_degree": round(avg_degree, 2),
        "max_degree": max_degree,
        "median_degree": median_degree,
        "gamma": round(gamma, 3),
        "r_squared": round(r_squared, 4),
        "is_scale_free": is_scale_free,
        "degree_data": [(k, pk) for k, pk in zip(ks, pks)],
        "log_slope": round(-gamma, 3),
        "log_intercept": round(intercept, 3),
        "top_hubs": [(name, deg) for name, deg in top_hubs],
    }


def generate_html_report(sw: dict, dd: dict, output: str = "output/small_world.html"):
    """Génère un rapport HTML interactif avec le thème Swiss Grid officiel."""

    degree_labels = json.dumps([d[0] for d in dd["degree_data"]])
    degree_values = json.dumps([round(d[1], 6) for d in dd["degree_data"]])
    hub_names = json.dumps([h[0].split("(")[0].strip() for h in dd["top_hubs"]])
    hub_degrees = json.dumps([h[1] for h in dd["top_hubs"]])

    sw_verdict = "OUI" if sw["is_small_world"] else "NON"
    sf_verdict = "OUI" if dd["is_scale_free"] else "NON"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#FFFFFF">
    <title>EPISTEME NETWORK</title>
    <link rel="icon" type="image/png" href="RSlogo.png">
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --bg: #FAFAFA;
            --text: #111111;
            --gray: #444444; 
            --line: rgba(0,0,0,0.08); 
            --glass: rgba(255, 255, 255, 0.85); 
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: transparent;
            color: var(--text);
            height: 100vh;
            overflow: hidden;
            font-size: 15px;
            -webkit-font-smoothing: antialiased;
        }}

        /* --- BACKGROUND --- */
        .aurora-container {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: 0;
            background: #FAFAFA;
            overflow: hidden;
        }}
        .orb {{
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.8;
            animation: float 20s infinite ease-in-out;
        }}
        .orb-1 {{ width: 60vw; height: 60vw; background: #E0E7FF; top: -20%; left: -10%; }}
        .orb-2 {{ width: 50vw; height: 50vw; background: #F0FDFA; bottom: -10%; right: -10%; animation-delay: -5s; }}
        .orb-3 {{ width: 40vw; height: 40vw; background: #F5F3FF; top: 40%; left: 40%; animation-delay: -10s; }}
        
        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) scale(1); }}
            33% {{ transform: translate(30px, -50px) scale(1.1); }}
            66% {{ transform: translate(-20px, 20px) scale(0.95); }}
        }}

        /* --- LAYOUT: SWISS GRID --- */
        .main-grid {{
            display: grid;
            grid-template-columns: 340px 1fr 340px;
            grid-template-rows: 1fr 60px;
            height: calc(100vh - 110px);
            width: 100vw;
            position: relative;
            z-index: 10;
            margin-top: 110px;
        }}

        /* Border Lines */
        .border-r {{ border-right: 1px solid var(--line); }}
        .border-b {{ border-bottom: 1px solid var(--line); }}
        .border-t {{ border-top: 1px solid var(--line); }}

        .sidebar-left {{
            grid-column: 1 / 2;
            grid-row: 1 / 2;
            padding: 48px 32px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            background: rgba(255,255,255,0.4);
            backdrop-filter: blur(10px);
            border-top: 1px solid var(--line);
        }}

        .content-center {{
            grid-column: 2 / 3;
            grid-row: 1 / 2;
            display: block;
            position: relative;
            border-top: 1px solid var(--line);
            overflow-y: auto;
            padding: 60px 48px;
        }}

        .sidebar-right {{
            grid-column: 3 / 4;
            grid-row: 1 / 2;
            padding: 48px 32px;
            display: flex;
            flex-direction: column;
            gap: 40px;
            background: rgba(255,255,255,0.4);
            backdrop-filter: blur(10px);
            border-top: 1px solid var(--line);
            border-left: 1px solid var(--line);
        }}

        .footer {{
            grid-column: 1 / 4;
            grid-row: 2 / 3;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            background: var(--glass);
            backdrop-filter: blur(20px);
            font-size: 13px;
            color: #555;
            font-weight: 500;
            border-top: 1px solid var(--line);
        }}

        /* Typography */
        h1 {{ font-size: 3rem; font-weight: 600; letter-spacing: -0.03em; margin-bottom: 24px; color: #000; }}
        h2 {{ font-size: 1.5rem; font-weight: 600; margin-bottom: 24px; margin-top: 48px; display: flex; align-items: center; gap: 12px; }}
        p {{ line-height: 1.7; color: #333; margin-bottom: 24px; max-width: 680px; }}
        
        .stat-block {{ margin-bottom: 24px; }}
        .stat-val {{ font-size: 2rem; font-weight: 600; display: block; color: #000; }}
        .stat-lbl {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #666; font-weight: 600; display: block; margin-bottom: 4px; }}

        /* Analysis Cards (Pipeline Step Style) */
        .analysis-card {{
            padding: 32px;
            background: rgba(255,255,255,0.3);
            border-radius: 16px;
            margin-bottom: 32px;
            border: 1px solid rgba(0,0,0,0.05);
        }}
        .analysis-card h3 {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 16px; display: flex; justify-content: space-between; }}
        .analysis-card .badge {{ font-size: 12px; padding: 4px 12px; border-radius: 100px; }}
        .badge-yes {{ background: #DCFCE7; color: #166534; }}
        .badge-no {{ background: #FEE2E2; color: #991B1B; }}

        .metric-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }}
        .metric-row:last-child {{ border-bottom: none; }}
        .metric-name {{ color: #666; font-size: 14px; }}
        .metric-data {{ font-weight: 600; font-variant-numeric: tabular-nums; }}

        .chart-wrapper {{ height: 300px; margin-top: 24px; position: relative; }}

        /* Scrollbar */
        .content-center::-webkit-scrollbar {{ width: 0px; background: transparent; }}

        @media (max-width: 1024px) {{
            .main-grid {{
                grid-template-columns: 1fr;
                grid-template-rows: auto auto auto auto;
                height: auto;
                overflow-y: auto;
                display: block;
                margin-top: 80px;
            }}
            .sidebar-left, .sidebar-right, .content-center {{ 
                grid-column: 1 / -1; 
                padding: 32px; 
                border: none;
                border-bottom: 1px solid var(--line);
            }}
        }}

        @media (max-width: 768px) {{
             body {{ overflow: auto !important; height: auto; }}
             .main-grid {{ margin-top: 0 !important; display: flex !important; flex-direction: column; }}
             .content-center {{ order: 1; padding: 24px !important; }}
             .sidebar-left {{ order: 2; padding: 24px !important; }}
             .sidebar-right {{ order: 3; padding: 24px !important; }}
             .footer {{ order: 4; }}
             h1 {{ font-size: 2.2rem !important; }}
        }}
    </style>
</head>
<body>
    <div id="app-header"></div>
    
    <div class="aurora-container">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    </div>

    <div class="main-grid">
        <!-- LEFT SIDEBAR -->
        <aside class="sidebar-left border-r">
            <div class="stat-block">
                <span class="stat-lbl">Analyse</span>
                <span class="stat-val" style="font-size: 1.5rem;">Topologie<br>Globale</span>
            </div>
            
            <div class="stat-block">
                <span class="stat-lbl">Nœuds</span>
                <span class="stat-val">{sw['n']}</span>
            </div>

            <div class="stat-block">
                <span class="stat-lbl">Liens</span>
                <span class="stat-val">{sw['m']}</span>
            </div>

            <div class="stat-block">
                <span class="stat-lbl">Densité</span>
                <span class="stat-val">{sw['density']:.5f}</span>
            </div>

            <div style="margin-top: auto;">
                <p style="font-size: 12px; color: #666;">
                    Analyse calculée sur la plus grande composante connexe du réseau.
                </p>
            </div>
        </aside>

        <!-- CENTER CONTENT -->
        <main class="content-center">
            <h1>Structure du Réseau</h1>
            <p style="font-size: 1.1rem; font-weight: 500; color: #000; margin-bottom: 48px;">
                Cette analyse vérifie si le graphe d'influence scientifique possède les propriétés mathématiques 
                d'un réseau "Petit Monde" et s'il suit une distribution "Scale-Free".
            </p>

            <h2><i data-lucide="network" style="width:24px;"></i> Small-World (Watts-Strogatz)</h2>
            <div class="analysis-card">
                <h3>
                    Verdict
                    <span class="badge { 'badge-yes' if sw['is_small_world'] else 'badge-no' }">{sw_verdict}</span>
                </h3>
                <p style="font-size: 14px;">
                    Un réseau "Petit Monde" se caractérise par une forte transitivité (clustering élevé) et des chemins courts.
                    Le coefficient Sigma (σ) > 1 confirme cette propriété.
                </p>
                
                <div class="metric-row">
                    <span class="metric-name">Coefficient de Clustering (C)</span>
                    <span class="metric-data">{sw['clustering_real']} <span style="color:#999; font-weight:400; font-size:12px;">(vs {sw['clustering_random']} rand)</span></span>
                </div>
                <div class="metric-row">
                    <span class="metric-name">Chemin Moyen (L)</span>
                    <span class="metric-data">{sw['path_length_real']} <span style="color:#999; font-weight:400; font-size:12px;">(vs {sw['path_length_random']} rand)</span></span>
                </div>
                <div class="metric-row">
                    <span class="metric-name" style="color:#111; font-weight:500;">Sigma (σ)</span>
                    <span class="metric-data" style="color:#2563EB;">{sw['sigma']}</span>
                </div>
            </div>

            <h2><i data-lucide="bar-chart-2" style="width:24px;"></i> Scale-Free (Loi de Puissance)</h2>
            <div class="analysis-card">
                <h3>
                    Verdict
                    <span class="badge { 'badge-yes' if dd['is_scale_free'] else 'badge-no' }">{sf_verdict}</span>
                </h3>
                <p style="font-size: 14px;">
                    La distribution des degrés suit une loi de puissance P(k) ∝ k^(-γ), ce qui indique la présence de "hubs" très connectés.
                </p>

                <div class="metric-row">
                    <span class="metric-name">Exposant Gamma (γ)</span>
                    <span class="metric-data">{dd['gamma']}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-name">Qualité de l'ajustement (R²)</span>
                    <span class="metric-data">{dd['r_squared']}</span>
                </div>
                
                <div class="chart-wrapper">
                    <canvas id="loglogChart"></canvas>
                </div>
            </div>

            <h2><i data-lucide="users" style="width:24px;"></i> Principaux Hubs</h2>
            <div class="analysis-card">
                <div class="chart-wrapper" style="height: 250px;">
                    <canvas id="hubsChart"></canvas>
                </div>
            </div>
        </main>

        <!-- RIGHT SIDEBAR -->
        <aside class="sidebar-right border-l">
            <div>
                <span class="stat-lbl">Interprétation</span>
                <p style="font-size: 13px; color: #444; margin-top: 12px;">
                    <b>Small World :</b> L'information circule très vite. Deux scientifiques quelconques sont séparés par seulement ~6 degrés, malgré la taille du réseau.
                </p>
                <p style="font-size: 13px; color: #444;">
                    <b>Scale Free :</b> Le réseau est robuste aux pannes aléatoires mais fragile aux attaques ciblées sur les hubs (ex: Einstein, Bohr).
                </p>
            </div>

            <div style="margin-top: auto;">
                <span class="stat-lbl">Graphe</span>
                <p style="font-size: 13px; font-weight: 500; margin-top: 4px;">Episteme Network</p>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                    <span style="padding: 4px 8px; background: rgba(0,0,0,0.05); border-radius: 4px; font-size: 11px;">Dirigé</span>
                    <span style="padding: 4px 8px; background: rgba(0,0,0,0.05); border-radius: 4px; font-size: 11px;">Pondéré</span>
                </div>
            </div>
        </aside>

        <!-- FOOTER -->
        <footer class="footer border-t">
            <span>© 2025 EPISTEME NETWORK</span>
            <div style="display: flex; gap: 24px;">
                <span>Projet Open Data</span>
                <span>L3 MIAGE</span>
            </div>
        </footer>
    </div>
    
    <script src="header.js?v=2.6"></script>
    <script>
        lucide.createIcons();
        
        // Chart.js Configuration
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#666';
        
        // Log-Log
        const degreeLabels = {degree_labels};
        const degreeValues = {degree_values};
        const logData = degreeLabels.map((k, i) => ({{
            x: k > 0 ? Math.log10(k) : null,
            y: degreeValues[i] > 0 ? Math.log10(degreeValues[i]) : null
        }})).filter(d => d.x !== null && d.y !== null);

        const xMin = Math.min(...logData.map(d => d.x));
        const xMax = Math.max(...logData.map(d => d.x));
        const slope = {dd['log_slope']};
        const intercept = {dd['log_intercept']};
        const regressionLine = [
            {{ x: xMin, y: slope * xMin + intercept }},
            {{ x: xMax, y: slope * xMax + intercept }}
        ];

        new Chart(document.getElementById('loglogChart'), {{
            type: 'scatter',
            data: {{
                datasets: [
                    {{
                        label: 'Distribution',
                        data: logData,
                        backgroundColor: '#111',
                        borderColor: '#111',
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }},
                    {{
                        label: 'Régression',
                        data: regressionLine,
                        type: 'line',
                        borderColor: '#999',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'log(Degré)' }}, grid: {{ color: '#eee' }} }},
                    y: {{ title: {{ display: true, text: 'log(Fréquence)' }}, grid: {{ color: '#eee' }} }}
                }}
            }}
        }});

        // Hubs
        new Chart(document.getElementById('hubsChart'), {{
            type: 'bar',
            data: {{
                labels: {hub_names},
                datasets: [{{
                    label: 'Connexions',
                    data: {hub_degrees},
                    backgroundColor: '#111',
                    borderRadius: 4,
                    barThickness: 20
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ color: '#eee' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ color: '#111', font: {{ weight: 500 }} }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  Page générée : {output}")


def main():
    print("=" * 60)
    print("  EPISTEME NETWORK — Analyse Small-World & Power Law")
    print("=" * 60)

    G_directed = load_graph()
    G = G_directed.to_undirected()

    print(f"\n  Graphe chargé : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")

    # 1. Analyse Small-World
    print("\n📐 ANALYSE SMALL-WORLD (Watts-Strogatz)")
    print("-" * 40)
    sw = small_world_analysis(G)

    print(f"\n  Clustering réel      : {sw['clustering_real']}")
    print(f"  Clustering aléatoire : {sw['clustering_random']}")
    print(f"  Ratio clustering     : {sw['clustering_ratio']}x")
    print(f"  Chemin moyen réel    : {sw['path_length_real']}")
    print(f"  Chemin moyen aléat.  : {sw['path_length_random']}")
    print(f"  Ratio chemin         : {sw['path_length_ratio']}x")
    print(f"  Sigma (σ)            : {sw['sigma']}")
    print(f"  Diamètre             : {sw['diameter']}")
    print(f"  → Small-World ?      : {'OUI' if sw['is_small_world'] else 'NON'}")

    # 2. Analyse Power Law (Distribution des Degrés)
    print("\n📊 ANALYSE POWER LAW (Barabási-Albert)")
    print("-" * 40)
    dd = degree_distribution_analysis(G)

    print(f"\n  Degré moyen          : {dd['avg_degree']}")
    print(f"  Degré médian         : {dd['median_degree']}")
    print(f"  Degré maximum        : {dd['max_degree']}")
    print(f"  Exposant gamma (γ)   : {dd['gamma']}")
    print(f"  R²                   : {dd['r_squared']}")
    print(f"  → Scale-Free ?       : {'OUI' if dd['is_scale_free'] else 'NON'}")

    print(f"\n  Top 10 Hubs :")
    for name, deg in dd["top_hubs"]:
        clean = name.split("(")[0].strip()
        print(f"    {clean:<28} {deg} connexions")

    # 3. Générer le rapport HTML
    print("\n📄 GÉNÉRATION DU RAPPORT HTML")
    print("-" * 40)
    generate_html_report(sw, dd)

    # Copier dans saves/version6
    save_path = "saves/version6/small_world.html"
    if os.path.exists("saves/version6"):
        import shutil
        shutil.copy2("output/small_world.html", save_path)
        print(f"  Copié dans : {save_path}")

    print("\n✅ Analyse terminée.")


if __name__ == "__main__":
    main()
