import ast
import networkx as nx
import plotly.graph_objects as go

def build_import_graph(sources: dict) -> nx.DiGraph:
    g = nx.DiGraph()
    names = set(sources)
    stem_to_file = {}
    for path in names:
        stem_to_file[path[:-3].replace("/", ".")] = path
        stem_to_file[path[:-3].replace("/", ".").replace(".","/", 99)] = path
    for path, source in sources.items():
        g.add_node(path)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            target = None
            if isinstance(node, ast.Import):
                for a in node.names:
                    target = a.name
                    candidate = next((p for p in names if p[:-3].replace("/", ".") == target), None)
                    if candidate:
                        g.add_edge(path, candidate)
            elif isinstance(node, ast.ImportFrom) and node.module:
                target = node.module
                candidate = next((p for p in names if p[:-3].replace("/", ".") == target), None)
                if candidate:
                    g.add_edge(path, candidate)
    return g

def graph_figure(g: nx.DiGraph):
    pos = nx.spring_layout(g, seed=42)
    edge_x, edge_y = [], []
    for a, b in g.edges():
        edge_x += [pos[a][0], pos[b][0], None]
        edge_y += [pos[a][1], pos[b][1], None]
    edge = go.Scatter(x=edge_x, y=edge_y, mode="lines", hoverinfo="none")
    nodes = list(g.nodes())
    node = go.Scatter(
        x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes],
        mode="markers+text", text=nodes, textposition="top center",
        hovertemplate="%{text}<extra></extra>", marker={"size": 18}
    )
    fig = go.Figure([edge, node])
    fig.update_layout(showlegend=False, margin=dict(l=10,r=10,t=10,b=10))
    return fig
