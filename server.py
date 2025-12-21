"""
Live Graph Generation Server
============================
Flask + WebSocket server for real-time graph visualization.
Streams node/edge additions as they happen during main.py execution.
"""

from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import subprocess
import threading
import json
import os
import time
import networkx as nx

app = Flask(__name__, static_folder='output', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
generation_process = None
generation_thread = None
is_generating = False

# Project paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
GEXF_PATH = os.path.join(OUTPUT_DIR, 'scientist_graph.gexf')


def get_current_graph():
    """Load current graph state from GEXF file."""
    if os.path.exists(GEXF_PATH):
        try:
            G = nx.read_gexf(GEXF_PATH)
            nodes = []
            edges = []
            
            for node_id, data in G.nodes(data=True):
                nodes.append({
                    'id': node_id,
                    'label': node_id,
                    'field': data.get('field', 'Unknown'),
                    'birth_year': data.get('birth_year'),
                    'death_year': data.get('death_year')
                })
            
            for source, target, data in G.edges(data=True):
                edges.append({
                    'from': source,
                    'to': target,
                    'type': data.get('relation_type', 'influenced')
                })
            
            return {'nodes': nodes, 'edges': edges}
        except Exception as e:
            print(f"Error loading graph: {e}")
            return {'nodes': [], 'edges': []}
    return {'nodes': [], 'edges': []}


def run_live_generation(start_scientist, max_nodes):
    """Run graph generation with live updates."""
    global is_generating
    is_generating = True
    
    # Import modules directly for live updates
    import sys
    sys.path.insert(0, PROJECT_DIR)
    
    from config import MAX_DEPTH
    from wikipedia_client import WikipediaClient
    from llm_extractor import LLMExtractor
    wiki = WikipediaClient()
    llm = LLMExtractor()
    
    # Use direct NetworkX graph for simplicity
    graph = nx.DiGraph()
    
    # BFS queue
    queue = [(start_scientist, 0)]
    visited = set()
    node_count = 0
    
    socketio.emit('generation_start', {
        'start': start_scientist,
        'max_nodes': max_nodes
    })
    
    while queue and node_count < max_nodes and is_generating:
        scientist, depth = queue.pop(0)
        
        if scientist in visited or depth > MAX_DEPTH:
            continue
        
        visited.add(scientist)
        
        # Emit progress
        socketio.emit('progress', {
            'current': scientist,
            'depth': depth,
            'visited': len(visited),
            'queue': len(queue),
            'max': max_nodes
        })
        
        # Fetch Wikipedia content
        result = wiki.get_scientist_text(scientist)
        if not result:
            continue
        
        content, links = result
        
        # Get scientific field
        field = wiki.get_scientific_field(scientist) or 'Unknown'
        
        # Add node with animation trigger
        node_data = {
            'id': scientist,
            'label': scientist,
            'field': field,
            'depth': depth
        }
        
        # Extract temporal data
        birth_year, death_year = wiki.extract_years(scientist)
        if birth_year:
            node_data['birth_year'] = birth_year
        if death_year:
            node_data['death_year'] = death_year
        
        graph.add_node(scientist, depth=depth, field=field)
        node_count += 1
        
        # Emit new node (with slight delay for animation)
        socketio.emit('new_node', node_data)
        time.sleep(0.3)  # Animation delay
        
        # Extract relations via LLM
        try:
            relations = llm.extract_relations(content, scientist, links=links)
            
            # Process inspirations (people who inspired this scientist)
            inspirations = relations.get('inspirations', [])
            for target in inspirations:
                if not target or target == scientist:
                    continue
                
                # Add edge: target -> scientist (target inspired scientist)
                graph.add_edge(target, scientist, relation='inspired')
                edge_data = {'from': target, 'to': scientist, 'type': 'inspired'}
                
                # Emit new edge
                socketio.emit('new_edge', edge_data)
                
                # Add to queue
                if target not in visited:
                    queue.append((target, depth + 1))
                    socketio.emit('queue_add', {'name': target, 'depth': depth + 1})
                
                time.sleep(0.1)
            
            # Process inspired (people this scientist inspired)
            inspired_list = relations.get('inspired', [])
            for target in inspired_list:
                if not target or target == scientist:
                    continue
                
                # Add edge: scientist -> target (scientist inspired target)
                graph.add_edge(scientist, target, relation='inspired')
                edge_data = {'from': scientist, 'to': target, 'type': 'inspired'}
                
                # Emit new edge
                socketio.emit('new_edge', edge_data)
                
                # Add to queue
                if target not in visited:
                    queue.append((target, depth + 1))
                    socketio.emit('queue_add', {'name': target, 'depth': depth + 1})
                
                time.sleep(0.1)
                    
        except Exception as e:
            socketio.emit('error', {'message': str(e), 'scientist': scientist})
            continue
        
        # Save checkpoint periodically
        if node_count % 10 == 0:
            nx.write_gexf(graph, GEXF_PATH)
            socketio.emit('checkpoint', {'nodes': node_count})
    
    # Final save
    nx.write_gexf(graph, GEXF_PATH)
    
    # Regenerate visualization (simplified for live mode)
    try:
        from visualizer import GraphVisualizer
        
        G = nx.read_gexf(GEXF_PATH)
        viz = GraphVisualizer(G)
        viz.create_interactive_html(os.path.join(OUTPUT_DIR, 'graph.html'))
        
        socketio.emit('viz_ready', {'url': '/graph.html'})
    except Exception as e:
        socketio.emit('error', {'message': f'Viz generation failed: {e}'})
    
    is_generating = False
    socketio.emit('generation_complete', {
        'total_nodes': node_count,
        'total_edges': graph.number_of_edges()
    })


@app.route('/')
def index():
    """Serve the landing page."""
    return send_from_directory('output', 'index.html')

@app.route('/graph.html')
def graph_page():
    """Serve the main visualization."""
    return send_from_directory('output', 'graph.html')


@app.route('/live')
def live():
    """Serve the live generation page."""
    return send_from_directory('output', 'live.html')


@app.route('/api/graph')
def api_graph():
    """Return current graph state as JSON."""
    return jsonify(get_current_graph())


@app.route('/api/status')
def api_status():
    """Return generation status."""
    return jsonify({
        'is_generating': is_generating,
        'graph': get_current_graph()
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")
    # Send current graph state
    emit('init', get_current_graph())


@socketio.on('start_generation')
def handle_start(data):
    """Start graph generation."""
    global generation_thread, is_generating
    
    if is_generating:
        emit('error', {'message': 'Generation already in progress'})
        return
    
    start_scientist = data.get('start', 'Albert Einstein')
    max_nodes = data.get('max_nodes', 100)
    
    generation_thread = threading.Thread(
        target=run_live_generation,
        args=(start_scientist, max_nodes)
    )
    generation_thread.daemon = True
    generation_thread.start()
    
    emit('started', {'start': start_scientist, 'max_nodes': max_nodes})


@socketio.on('stop_generation')
def handle_stop():
    """Stop graph generation."""
    global is_generating
    is_generating = False
    emit('stopped', {'message': 'Generation stopped by user'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected")


if __name__ == '__main__':
    print("🚀 Starting Live Graph Server...")
    print("   Open http://localhost:5050/live for live visualization")
    print("   Open http://localhost:5050/ for static visualization")
    socketio.run(app, host='0.0.0.0', port=5050, debug=True)
