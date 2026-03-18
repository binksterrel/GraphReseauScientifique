import networkx as nx
import math
import json
import os
import random
from collections import Counter
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)


class GraphAnalyzer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.results: dict = {}

    def analyze(self) -> dict:
        G = self.graph
        n = G.number_of_nodes()
        m = G.number_of_edges()
        logger.info(f"GraphAnalyzer: {n} noeuds, {m} aretes")

        if n < 5:
            logger.warning("Graphe trop petit pour l'analyse.")
            return {}

        G_und = G.to_undirected()

        # --- 1. Small World (Watts-Strogatz) ---
        C = nx.average_clustering(G_und)
        degrees = [d for _, d in G_und.degree()]
        avg_k = sum(degrees) / n if n > 0 else 0

        # Baselines graphe aléatoire (Erdős–Rényi)
        C_rand = avg_k / n if n > 0 else 0
        L_rand = math.log(n) / math.log(avg_k) if avg_k > 1 else float('inf')

        # Chemin moyen sur la composante connexe principale (LCC), par échantillonnage
        components = list(nx.connected_components(G_und))
        lcc_nodes = max(components, key=len)
        G_lcc = G_und.subgraph(lcc_nodes)
        lcc_size = len(lcc_nodes)

        SAMPLE_SIZE = 200
        sample_nodes = (
            random.sample(list(lcc_nodes), SAMPLE_SIZE)
            if lcc_size > SAMPLE_SIZE
            else list(lcc_nodes)
        )

        total_length = 0
        count = 0
        for src in sample_nodes:
            lengths = nx.single_source_shortest_path_length(G_lcc, src)
            for dst, length in lengths.items():
                if dst != src:
                    total_length += length
                    count += 1

        L = total_length / count if count > 0 else float('inf')

        # Sigma (σ) : indicateur Small World
        if C_rand > 0 and L_rand not in (float('inf'), 0) and L not in (float('inf'), 0):
            sigma = (C / C_rand) / (L / L_rand)
        else:
            sigma = 0.0

        # --- 2. Scale-Free (loi de puissance) ---
        degree_count = Counter(degrees)
        total_nodes = sum(degree_count.values())
        degree_dist = {k: v / total_nodes for k, v in degree_count.items() if k > 0}

        log_k = [math.log10(k) for k in degree_dist]
        log_p = [math.log10(p) for p in degree_dist.values()]
        n_pts = len(log_k)

        if n_pts >= 2:
            mean_x = sum(log_k) / n_pts
            mean_y = sum(log_p) / n_pts
            ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_k, log_p))
            ss_xx = sum((x - mean_x) ** 2 for x in log_k)
            slope = ss_xy / ss_xx if ss_xx != 0 else 0
            intercept = mean_y - slope * mean_x
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(log_k, log_p))
            ss_tot = sum((y - mean_y) ** 2 for y in log_p)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        else:
            slope, intercept, r2 = 0.0, 0.0, 0.0

        gamma = -slope

        # --- 3. Hubs principaux (degré total sur graphe dirigé) ---
        degree_dict = dict(G.degree())
        top_hubs = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:10]

        self.results = {
            'n_nodes': n,
            'n_edges': m,
            'lcc_size': lcc_size,
            'lcc_ratio': round(lcc_size / n, 3),
            'avg_degree': round(avg_k, 2),
            'clustering': round(C, 4),
            'clustering_rand': round(C_rand, 4),
            'avg_path_length': round(L, 2),
            'avg_path_length_rand': round(L_rand, 2),
            'sigma': round(sigma, 2),
            'is_small_world': sigma > 1,
            'gamma': round(gamma, 3),
            'r2': round(r2, 4),
            'is_scale_free': 2.0 <= gamma <= 3.5 and r2 > 0.7,
            'top_hubs': [[name, deg] for name, deg in top_hubs],
            'degree_distribution': sorted([[k, p] for k, p in degree_dist.items()]),
            'slope': round(slope, 3),
            'intercept': round(intercept, 3),
        }

        logger.info(
            f"Small World: σ={sigma:.2f}, C={C:.4f} (rand={C_rand:.4f}), "
            f"L={L:.2f} (rand={L_rand:.2f})"
        )
        logger.info(f"Scale Free: γ={gamma:.3f}, R²={r2:.4f}")
        if top_hubs:
            logger.info(f"Hub principal: {top_hubs[0][0]} ({top_hubs[0][1]} connexions)")

        return self.results

    def save_results(self, output_path: str = "output/analysis.json") -> None:
        """Exporte les métriques en JSON."""
        if not self.results:
            logger.warning("Aucun résultat à exporter. Lancez analyze() d'abord.")
            return
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        logger.info(f"Analyse exportée vers: {output_path}")

    def generate_small_world_html(
        self,
        template_path: str = "docs/small_world.html",
        output_path: str = "output/small_world.html",
    ) -> None:
        """Met à jour small_world.html avec les métriques calculées."""
        if not self.results:
            logger.warning("Aucun résultat. Lancez analyze() d'abord.")
            return

        r = self.results

        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # --- Remplacement des métriques Small World ---
        sw_verdict = "OUI" if r['is_small_world'] else "NON"
        sw_badge_class = "badge-yes" if r['is_small_world'] else "badge-no"
        sf_verdict = "OUI" if r['is_scale_free'] else "NON"
        sf_badge_class = "badge-yes" if r['is_scale_free'] else "badge-no"

        # Clustering
        html = html.replace(
            f'>{r.get("_old_clustering", "0.0702")} <span style="color:#999; font-weight:400; font-size:12px;">(vs {r.get("_old_c_rand", "0.0014")} rand)</span><',
            f'>{r["clustering"]} <span style="color:#999; font-weight:400; font-size:12px;">(vs {r["clustering_rand"]} rand)</span><'
        )

        # Génération du bloc JavaScript data uniquement
        hub_labels = json.dumps([h[0] for h in r['top_hubs']])
        hub_data = json.dumps([h[1] for h in r['top_hubs']])
        deg_labels = json.dumps([int(d[0]) for d in r['degree_distribution']])
        deg_values = json.dumps([round(d[1], 6) for d in r['degree_distribution']])

        new_script = f"""
        lucide.createIcons();

        // Chart.js Configuration
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#666';

        // Log-Log
        const degreeLabels = {deg_labels};
        const degreeValues = {deg_values};
        const logData = degreeLabels.map((k, i) => ({{
            x: k > 0 ? Math.log10(k) : null,
            y: degreeValues[i] > 0 ? Math.log10(degreeValues[i]) : null
        }})).filter(d => d.x !== null && d.y !== null);

        const xMin = Math.min(...logData.map(d => d.x));
        const xMax = Math.max(...logData.map(d => d.x));
        const slope = {r['slope']};
        const intercept = {r['intercept']};
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
                labels: {hub_labels},
                datasets: [{{
                    label: 'Connexions',
                    data: {hub_data},
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
"""

        # Remplacer le bloc <script> existant
        import re
        html = re.sub(
            r'(<script src="header\.js[^"]*"></script>\s*<script>)(.*?)(</script>)',
            lambda m: m.group(1) + new_script + m.group(3),
            html,
            flags=re.DOTALL
        )

        # Remplacer les valeurs métriques dans le HTML
        replacements = [
            # Clustering
            (
                f'0.0702 <span style="color:#999; font-weight:400; font-size:12px;">(vs 0.0014 rand)</span>',
                f'{r["clustering"]} <span style="color:#999; font-weight:400; font-size:12px;">(vs {r["clustering_rand"]} rand)</span>'
            ),
            # Chemin moyen
            (
                f'6.67 <span style="color:#999; font-weight:400; font-size:12px;">(vs 6.99 rand)</span>',
                f'{r["avg_path_length"]} <span style="color:#999; font-weight:400; font-size:12px;">(vs {r["avg_path_length_rand"]} rand)</span>'
            ),
            # Sigma
            ('style="color:#2563EB;">51.53', f'style="color:#2563EB;">{r["sigma"]}'),
            # Gamma
            ('<span class="metric-data">2.138</span>', f'<span class="metric-data">{r["gamma"]}</span>'),
            # R²
            ('<span class="metric-data">0.9225</span>', f'<span class="metric-data">{r["r2"]}</span>'),
            # Badge Small World
            (
                f'<span class="badge badge-yes">OUI</span>\n                </h3>\n                <p style="font-size: 14px;">\n                    Un réseau "Petit Monde"',
                f'<span class="badge {sw_badge_class}">{sw_verdict}</span>\n                </h3>\n                <p style="font-size: 14px;">\n                    Un réseau "Petit Monde"'
            ),
            # Badge Scale Free
            (
                f'<span class="badge badge-yes">OUI</span>\n                </h3>\n                <p style="font-size: 14px;">\n                    La distribution',
                f'<span class="badge {sf_badge_class}">{sf_verdict}</span>\n                </h3>\n                <p style="font-size: 14px;">\n                    La distribution'
            ),
        ]

        for old, new in replacements:
            html = html.replace(old, new)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"small_world.html généré vers: {output_path}")
