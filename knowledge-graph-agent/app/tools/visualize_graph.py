import networkx as nx
import numpy as np
from networkx.algorithms.community.louvain import louvain_communities
import textwrap
from typing import cast, Iterator, Any
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
from PIL import Image as PilImage
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from io import BytesIO
import matplotlib
import os
import uuid
from google.cloud import storage

# Set non-interactive backend
matplotlib.use('Agg')

# Constants
NODE_CENTRALITY = "node_centrality"
NODE_COMMUNITY_INDEX = "node_community_index"
NODE_COLOR = "node_color"
EDGE_COLOR = "edge_color"
MULTILINE_NAMES = True
MULTILINE_CHARS = 12

Node = str
Positions = dict[Node, np.ndarray]
Community = set[Node]
Communities = list[Community]
Nodes = list[Node]
INTER_COMMUNITY_EDGE_COLOR = "#8888"

FIGURE_DPI = 200
FIGURE_FACTOR = 1.0
ANIMATION_INTRO_DURATION = 2500
ANIMATION_FRAME_DURATION = 250
EDGE_STYLE = "arc3,rad=0.2"
NodeSizes = dict[Node, int]

def get_node_and_display_names_for_entity(entity: dict) -> tuple[str, str]:
    entity_id = entity.get("id", "")
    entity_name = entity.get("name", "")
    snake_case_name = "_".join(map(str.lower, str(entity_name).split()))
    node_name = f"{entity_id}_{snake_case_name}"

    display_name = str(entity_name)
    if MULTILINE_NAMES:
        display_name = "\n".join(textwrap.wrap(display_name, width=MULTILINE_CHARS))

    return node_name, display_name

def build_graph(entities: list[dict], relationships: list[dict], remove_orphan_nodes: bool) -> nx.DiGraph:
    graph = nx.DiGraph()

    node_name_from_id: dict[Any, str] = {}
    for entity in entities:
        node_name, display_name = get_node_and_display_names_for_entity(entity)
        node_name_from_id[entity.get("id")] = node_name
        graph.add_node(node_name, name=display_name)

    for relationship in relationships:
        source_id = relationship.get("source_id")
        target_id = relationship.get("target_id")
        
        source_node = node_name_from_id.get(source_id, "")
        target_node = node_name_from_id.get(target_id, "")
        if not source_node or not target_node:
            print(f"❌ Skipping relationship due to empty node:\n{relationship}")
            continue
            
        weight = 1
        edge_label = relationship.get("link", "")
        if graph.has_edge(source_node, target_node):
            existing_data = graph[source_node][target_node]
            existing_data["link"] += f"\n{edge_label}"
            existing_data["weight"] += weight
        else:
            graph.add_edge(source_node, target_node, link=edge_label, weight=weight)

    if remove_orphan_nodes:
        graph.remove_nodes_from(list(nx.isolates(graph)))

    return graph

def color_gen(color_count: int) -> Iterator[str]:
    B50, R50, Y50, G50 = ("#4285F4", "#EA4335", "#FBBC04", "#34A853")
    B20, R20, Y20, G20 = ("#AECBFA", "#F6AEA9", "#FDE293", "#A8DAB5")
    B05, R05, Y05, G05 = ("#E8F0FE", "#FCE8E6", "#FEF7E0", "#E6F4EA")
    COLORS = [B50, R50, Y50, G50, B20, R20, Y20, G20, B05, R05, Y05, G05]
    for i in range(color_count):
        yield COLORS[i % len(COLORS)]

def init_graph_data(graph: nx.Graph) -> Nodes:
    def node_centrality(node: Node) -> float:
        return graph.nodes[node][NODE_CENTRALITY]

    def community_max_centrality(community: Community) -> float:
        return max((node_centrality(node) for node in community), default=0)

    def nodes_sorted_by_community(communities: Communities) -> Nodes:
        entities = []
        for community in communities:
            sorted_entities = sorted(community, key=node_centrality, reverse=True)
            entities.extend(sorted_entities)
        return entities

    centralities = nx.betweenness_centrality(graph, endpoints=True)
    for node_key in graph.nodes:
        graph.nodes[node_key][NODE_CENTRALITY] = centralities[node_key]

    communities = cast(Communities, louvain_communities(graph, seed=42))
    sorted_communities = sorted(communities, key=community_max_centrality, reverse=True)

    community_count = len(sorted_communities)
    community_colors = list(color_gen(community_count))

    for community_index, community in enumerate(sorted_communities):
        for node_key in community:
            node = graph.nodes[node_key]
            node[NODE_COMMUNITY_INDEX] = community_index
            node[NODE_COLOR] = community_colors[community_index]

    for node_key_i, node_key_j, edge_data in graph.edges(data=True):
        node_i = graph.nodes[node_key_i]
        node_j = graph.nodes[node_key_j]
        same_community = node_i[NODE_COMMUNITY_INDEX] == node_j[NODE_COMMUNITY_INDEX]
        edge_data[EDGE_COLOR] = (
            node_i[NODE_COLOR] if same_community else INTER_COMMUNITY_EDGE_COLOR
        )

    return nodes_sorted_by_community(sorted_communities)

def compute_node_positions(graph: nx.DiGraph, entities: Nodes) -> Positions:
    undirected_graph = nx.Graph()
    for entity in entities:
        undirected_graph.add_node(entity)
    undirected_graph.add_edges_from(graph.edges())

    if len(entities) < 10:
        positions = nx.circular_layout(undirected_graph)
    else:
        positions = nx.kamada_kawai_layout(undirected_graph)
        positions = nx.arf_layout(undirected_graph, positions, seed=42)

    return positions

@dataclass
class GraphData:
    entities: list[dict]
    relationships: list[dict]
    remove_orphan_nodes: bool = True
    graph: nx.DiGraph = field(init=False)
    nodes: Nodes = field(init=False)
    positions: Positions = field(init=False)

    def __post_init__(self) -> None:
        self.graph = build_graph(self.entities, self.relationships, self.remove_orphan_nodes)
        self.nodes = init_graph_data(self.graph)
        self.positions = compute_node_positions(self.graph, self.nodes)

def init_figure(title: str, subtitle: str) -> tuple[Figure, Axes]:
    figsize = (16 * FIGURE_FACTOR, 9 * FIGURE_FACTOR)
    fig, ax = plt.subplots(figsize=figsize, dpi=FIGURE_DPI)
    ax.set_title(title, loc="left")
    ax.set_title(subtitle, loc="right")
    ax.axis("off")
    fig.tight_layout(pad=2)

    return fig, ax

def draw_nodes(graph: nx.Graph, positions: Positions, ax: Axes) -> NodeSizes:
    node_view = graph.nodes(data=True)
    node_sizes = {
        node: max(500, int(10000 * data[NODE_CENTRALITY])) for node, data in node_view
    }
    node_colors = [str(data[NODE_COLOR]) for _, data in node_view]
    border_width = 3.0

    nx.draw_networkx_nodes(
        graph,
        pos=positions,
        node_size=list(node_sizes.values()),
        node_color=node_colors,
        alpha=0.95,
        ax=ax,
        linewidths=border_width,
    )
    labels = {node: data.get("name", str(node)) for node, data in node_view}
    nx.draw_networkx_labels(graph, positions, labels=labels, ax=ax)

    if len(node_sizes) >= 10:
        (x_min, x_max), (y_min, y_max) = ax.get_xlim(), ax.get_ylim()
        x_min, x_max = int(x_min - 1.0), int(x_max + 1.0)
        y_min, y_max = int(y_min - 1.0), int(y_max + 1.0)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

    return node_sizes

def draw_edges(
    graph: nx.DiGraph,
    positions: Positions,
    node_sizes: NodeSizes,
    ax: Axes,
    *,
    focused_node: Node | None = None,
) -> None:
    if focused_node:
        out_edges = graph.edges([focused_node], data=True)
    else:
        out_edges = graph.edges(data=True)
    edge_colors = [data[EDGE_COLOR] for _, _, data in out_edges]

    edge_list = [(u, v) for u, v, _ in out_edges]
    ordered_sizes = [node_sizes[n] for n in graph.nodes()]
    nx.draw_networkx_edges(
        graph,
        positions,
        edge_list,
        edge_color=edge_colors,
        style=":",
        alpha=0.9,
        arrowstyle="-|>",
        arrowsize=20,
        ax=ax,
        node_size=ordered_sizes,
        connectionstyle=EDGE_STYLE,
    )

    edge_labels = {(u, v): data["link"] for u, v, data in out_edges}
    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels,
        font_size=8,
        font_family="monospace",
        bbox=dict(ec="#FFF8", fc="#FFF8"),
        ax=ax,
        node_size=ordered_sizes,  # type: ignore
        connectionstyle=EDGE_STYLE,  # type: ignore
    )

def yield_images(
    title: str,
    subtitle: str,
    graph_data: GraphData,
) -> Iterator[PilImage.Image]:
    fig, ax = init_figure(title, subtitle)
    canvas = FigureCanvasAgg(fig)

    positions = graph_data.positions
    node_graph = graph_data.graph
    node_sizes = draw_nodes(node_graph, positions, ax)
    edge_graph = graph_data.graph

    for focused_node in [None, *graph_data.nodes]:
        if focused_node is not None:
            draw_edges(edge_graph, positions, node_sizes, ax, focused_node=focused_node)
        canvas.draw()
        image_size = canvas.get_width_height()
        image_bytes = canvas.buffer_rgba()
        yield PilImage.frombytes("RGBA", image_size, image_bytes).convert("RGB")
    plt.close(fig)

def generate_animation(
    title: str,
    subtitle: str,
    graph_data: GraphData,
    format: str = "WEBP",
) -> BytesIO:
    frames = list(yield_images(title, subtitle, graph_data))
    if not frames:
        raise ValueError("No frames generated")

    if format.upper() == "GIF":
        method = PilImage.Quantize.MEDIANCUT
        palettized = frames[-1].quantize(method=method)
        frames = [frame.quantize(method=method, palette=palettized) for frame in frames]

    first_frame = frames[-1]
    next_frames = frames[:-1]
    durations = [ANIMATION_INTRO_DURATION]
    durations += [ANIMATION_FRAME_DURATION] * len(next_frames)
    params: dict[str, Any] = dict(
        save_all=True,
        append_images=next_frames,
        duration=durations,
        loop=0,
    )
    if format.upper() == "GIF":
        params.update(optimize=False)
    elif format.upper() == "PNG":
        params.update(optimize=True)
    elif format.upper() == "WEBP":
        params.update(lossless=True)

    image_io = BytesIO()
    first_frame.save(image_io, format.upper(), **params)
    return image_io

from google.adk.tools import ToolContext
from google.genai import types

async def visualize_knowledge_graph(
    entities: list[dict],
    relationships: list[dict],
    title: str = "Knowledge Graph",
    subtitle: str = "Generated Visualization",
    output_filename: str = "knowledge_graph.webp",
    tool_context: ToolContext = None
) -> str:
    """Generates an animated representation of the knowledge graph and saves it to a file.
    
    Args:
        entities: List of entity dictionaries with keys like 'id', 'name', 'label'.
        relationships: List of relationship dictionaries with keys 'source_id', 'target_id', 'link'.
        title: Title of the graph to display.
        subtitle: Subtitle of the graph to display.
        output_filename: The local filename where the animation will be saved. Must be .webp, .gif, or .png.
        tool_context: Internal ADK context to save artifacts.
        
    Returns:
        The path to the generated visualization file.
    """
    ext = output_filename.split(".")[-1].upper()
    if ext not in ("WEBP", "PNG", "GIF"):
        ext = "WEBP"
        
    if not entities:
        return "Error: No entities provided to visualize."

    graph_data = GraphData(entities=entities, relationships=relationships)
    
    # Generate animation in memory
    image_io = generate_animation(title, subtitle, graph_data, format=ext)
    
    # Save to disk locally
    image_bytes = image_io.getvalue()
    with open(output_filename, "wb") as f:
        f.write(image_bytes)
        
    # Save to ADK artifacts registry if available
    if tool_context:
        try:
            content_type = f"image/{ext.lower()}"
            part = types.Part(inline_data=types.Blob(mime_type=content_type, data=image_bytes))
            await tool_context.save_artifact(filename=output_filename, artifact=part)
            print(f"✅ Successfully saved {output_filename} to ADK artifacts registry.")
        except Exception as e:
            print(f"⚠️ Failed to save to ADK artifacts registry: {e}")
            
    try:
        bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "ml-demo-384110-agent-engine")
        if bucket_name.startswith("gs://"):
            bucket_name = bucket_name[5:]
            
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        blob_name = f"knowledge_graphs/{uuid.uuid4().hex[:8]}_{output_filename}"
        blob = bucket.blob(blob_name)
        
        content_type = f"image/{ext.lower()}"
        blob.upload_from_string(image_bytes, content_type=content_type)
        
        gcs_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
        return f"Visualization successfully generated. Access it here: {gcs_url}"
    except Exception as e:
        return f"Visualization generated and saved locally to {output_filename}, but failed to upload to Google Cloud Storage: {str(e)}"
