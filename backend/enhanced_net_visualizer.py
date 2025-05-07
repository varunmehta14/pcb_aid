import networkx as nx
import matplotlib.pyplot as plt
import math
import os
from trace_extractor import PCBTraceExtractor, Pad, Track, Arc, Via, MILS_TO_MM, CONNECT_TOLERANCE

def visualize_net(comp1, pad1, comp2, pad2, json_file="Vacuum_PCB_OBjects.json", 
                 save_path="net_visualization.png", debug=False, show_labels=True):
    """
    Visualize the network graph for a specific net, highlighting the path between two pads.
    Enhanced with accurate length labels for path segments.
    
    Args:
        comp1: First component designator
        pad1: First pad number
        comp2: Second component designator
        pad2: Second pad number
        json_file: Path to the PCB JSON file
        save_path: Path to save the visualization image
        debug: Whether to print detailed debug information
        show_labels: Whether to show node labels in the visualization
    """
    # Initialize extractor and load data
    extractor = PCBTraceExtractor()
    extractor.load_json_file(json_file)
    
    # First run the extractor to get the actual trace length
    trace_length = extractor.extract_traces_between_pads(comp1, pad1, comp2, pad2, debug=debug)
    if trace_length is None:
        print(f"Error: No valid trace found between {comp1}.{pad1} and {comp2}.{pad2}")
        return None
    
    # Find the pads
    pad_a = next((p for p in extractor.pads if p.designator==comp1 and p.pad_number==pad1), None)
    pad_b = next((p for p in extractor.pads if p.designator==comp2 and p.pad_number==pad2), None)
    
    if not pad_a or not pad_b:
        print(f"Error: Could not find one or both pads: {comp1}.{pad1} or {comp2}.{pad2}")
        return None
    
    if pad_a.net_name != pad_b.net_name:
        print(f"Error: Pads are on different nets: {pad_a.net_name} vs {pad_b.net_name}")
        return None
    
    # Get all objects in the same net
    net_name = pad_a.net_name
    net_objs = [o for o in extractor.objects if o.net_name == net_name]
    
    # Build the graph
    G = nx.Graph()
    G.add_nodes_from(net_objs)
    
    # Add edges for connected objects
    for i, o1 in enumerate(net_objs):
        for o2 in net_objs[i+1:]:
            if o1.is_connected(o2):
                # Calculate weight based on length
                if isinstance(o1, (Track, Arc)):
                    weight = o1.length * MILS_TO_MM
                elif isinstance(o2, (Track, Arc)):
                    weight = o2.length * MILS_TO_MM
                else:
                    weight = 0.0001  # Default minimal weight
                
                G.add_edge(o1, o2, weight=weight)
    
    # Find shortest path between pads if connected
    try:
        path = nx.shortest_path(G, pad_a, pad_b, weight='weight')
        
        # Don't use nx.shortest_path_length as it might not match the extractor's calculation
        print(f"Found path with {len(path)} nodes")
        if debug:
            print(f"Path: {' -> '.join(str(o) for o in path)}")
    except nx.NetworkXNoPath:
        print("No path found between the pads!")
        return None
    
    # Create visualization
    plt.figure(figsize=(14, 12))
    
    # Group nodes by type
    node_groups = {
        'Pads': [n for n in G.nodes() if isinstance(n, Pad)],
        'Tracks': [n for n in G.nodes() if isinstance(n, Track)],
        'Arcs': [n for n in G.nodes() if isinstance(n, Arc)],
        'Vias': [n for n in G.nodes() if isinstance(n, Via)]
    }
    
    # Color map for node types
    color_map = {
        'Pads': 'skyblue',
        'Tracks': 'limegreen',
        'Arcs': 'orange',
        'Vias': 'red'
    }
    
    # Node size map
    size_map = {
        'Pads': 120,
        'Tracks': 60,
        'Arcs': 80,
        'Vias': 100
    }
    
    # Create position mapping based on object geometry
    pos = {}
    for node in G.nodes():
        if hasattr(node, 'location'):
            pos[node] = node.location
        elif hasattr(node, 'start') and hasattr(node, 'end'):
            # For tracks and arcs, use midpoint
            pos[node] = ((node.start[0] + node.end[0])/2, 
                         (node.start[1] + node.end[1])/2)
    
    # Draw nodes by type
    for node_type, nodes in node_groups.items():
        if nodes:
            # Make path nodes slightly larger
            sizes = [size_map[node_type] * 1.5 if n in path else size_map[node_type] for n in nodes]
            
            nx.draw_networkx_nodes(G, pos, 
                                   nodelist=nodes, 
                                   node_color=color_map[node_type], 
                                   node_size=sizes, 
                                   label=node_type,
                                   alpha=0.7)
    
    # Create path edges
    path_edges = list(zip(path, path[1:]))
    
    # Draw non-path edges first (as background)
    other_edges = [e for e in G.edges() if e not in path_edges and (e[1], e[0]) not in path_edges]
    if other_edges:
        nx.draw_networkx_edges(G, pos, 
                              edgelist=other_edges, 
                              edge_color='darkgray', 
                              width=1, 
                              alpha=0.4,
                              label='Other Connections')
    
    # Draw path edges prominently
    nx.draw_networkx_edges(G, pos, 
                           edgelist=path_edges, 
                           edge_color='crimson', 
                           width=3,
                           label='Path')

    # --- Add edge length labels for the path ---
    # Track individual segment lengths and their cumulative total
    edge_labels = {}
    segment_lengths = []
    
    # Create a dictionary to track which tracks/arcs have already been accounted for
    processed_tracks = set()
    
    # First analysis pass - identify all tracks/arcs and their contribution to the path
    track_segments = []
    
    for i in range(len(path)):
        node = path[i]
        if isinstance(node, (Track, Arc)):
            track_segments.append((i, node))
    
    if debug:
        print("\nTrack/Arc segments in path:")
        for idx, track in track_segments:
            print(f"  Position {idx}: {track}")
    
    # Better approach: analyze the path once to identify which elements contribute to the length
    # We'll use the path from trace_extractor as the source of truth
    expected_length = trace_length
    computed_length = 0.0
    
    # Maps segments to their contributing length to avoid double counting
    segment_to_length = {}
    
    # Process each segment in the path
    for i in range(len(path) - 1):
        src = path[i]
        tgt = path[i + 1]
        edge_key = (src, tgt)
        
        # Skip labeling certain transitions to avoid double counting
        # For example, if we have a Pad->Track->Track->Pad path and both tracks have the
        # same length, we might want to only label one of them to match the extractor's calculation
        
        # Identify the actual contributor to the length for this edge
        segment_length_mm = None
        contributor = None
        
        # Case 1: Pad/Via to Track/Arc - the track/arc contributes
        if isinstance(src, (Pad, Via)) and isinstance(tgt, (Track, Arc)):
            if tgt not in processed_tracks:
                segment_length_mm = tgt.length * MILS_TO_MM
                contributor = tgt
                processed_tracks.add(tgt)
        
        # Case 2: Track/Arc to Pad/Via - the track/arc contributes if not already counted
        elif isinstance(src, (Track, Arc)) and isinstance(tgt, (Pad, Via)):
            if src not in processed_tracks:
                segment_length_mm = src.length * MILS_TO_MM
                contributor = src
                processed_tracks.add(src)
        
        # Case 3: Track/Arc to Track/Arc - this is the tricky case that causes double counting
        elif isinstance(src, (Track, Arc)) and isinstance(tgt, (Track, Arc)):
            # Only include one of them if not yet processed
            if src not in processed_tracks:
                segment_length_mm = src.length * MILS_TO_MM
                contributor = src
                processed_tracks.add(src)
                # Special case: if next track is the same length, mark it as processed too
                if abs(src.length - tgt.length) < 0.01:
                    processed_tracks.add(tgt)
        
        # Add to segment lengths if we found a valid contributor
        if segment_length_mm is not None and segment_length_mm > 0:
            segment_lengths.append(segment_length_mm)
            computed_length += segment_length_mm
            segment_to_length[edge_key] = segment_length_mm
            
            # Add the edge label
            edge_labels[edge_key] = f"{segment_length_mm:.2f} mm"
    
    # Safety check: if we're way off, adjust our calculation to match extractor's
    if segment_lengths and abs(computed_length - expected_length) > 0.01:
        # Calculate the scaling factor to match expected length
        if debug:
            print(f"\nCalculated length ({computed_length:.2f} mm) differs from expected ({expected_length:.2f} mm)")
            
        # If we're way off, attempt to reconcile by looking at missing segments or double counting
        discrepancy = computed_length - expected_length
        
        # Check if the discrepancy matches any segment, which would suggest double counting
        for length in segment_lengths:
            if abs(discrepancy - length) < 0.01:
                if debug:
                    print(f"Discrepancy matches segment length {length:.2f} mm - likely double counted")
                break
    
    # Add the edge labels to the visualization
    if edge_labels:
        nx.draw_networkx_edge_labels(
            G, pos,
            edge_labels=edge_labels,
            font_size=8,
            font_color='darkblue',
            font_weight='bold',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=2),
            rotate=False
        )
    
    # Highlight source and target nodes
    nx.draw_networkx_nodes(G, pos, 
                           nodelist=[pad_a], 
                           node_color='purple', 
                           node_size=200, 
                           label=f'Source: {comp1}.{pad1}')
    nx.draw_networkx_nodes(G, pos, 
                           nodelist=[pad_b], 
                           node_color='yellow', 
                           node_size=200, 
                           label=f'Target: {comp2}.{pad2}')
    
    # Add labels based on user preference
    if show_labels:
        # Add basic type labels to path objects
        type_labels = {node: f"{type(node).__name__}" for node in path 
                     if isinstance(node, (Track, Arc, Via))}
        
        # Add component and pad info for pads
        pad_labels = {node: f"{node.designator}.{node.pad_number}" 
                     for node in node_groups['Pads'] 
                     if node in path or node==pad_a or node==pad_b}
        
        # Combine all labels
        all_labels = {**type_labels, **pad_labels}
        
        # Draw the labels
        nx.draw_networkx_labels(G, pos, all_labels, font_size=8)
    
    # Check if segments add up to the extracted length
    title_suffix = ""
    if segment_lengths and abs(computed_length - trace_length) > 0.01:
        title_suffix = f"\nNote: Segment sum ({computed_length:.2f} mm) ≠ Reported length ({trace_length:.2f} mm)"
    
    # Title and finishing touches
    plt.title(f"Trace Path: {comp1}.{pad1} → {comp2}.{pad2}\nNet: {net_name} | Length: {trace_length:.5f} mm{title_suffix}", 
             fontsize=14)
    plt.legend(loc="upper right", scatterpoints=1)
    plt.axis('off')
    plt.grid(False)
    
    # Create output directory if needed
    output_dir = os.path.dirname(save_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save figure
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved as '{save_path}'")
    plt.close()

    # Print debug info
    if debug and segment_lengths:
        print("\nSegment lengths analysis:")
        print(f"- Individual segments: {', '.join([f'{l:.2f}' for l in segment_lengths])} mm")
        print(f"- Sum of segments: {computed_length:.2f} mm")
        print(f"- Trace length from extractor: {trace_length:.2f} mm")
        
        if abs(computed_length - trace_length) > 0.01:
            discrepancy = abs(computed_length - trace_length)
            print(f"\nWARNING: Difference between calculated and reported length: {discrepancy:.2f} mm")
            
            # Check if discrepancy matches any segment
            for length in segment_lengths:
                if abs(discrepancy - length) < 0.01:
                    print(f"  Note: Discrepancy matches segment length {length:.2f} mm, possibly double-counted")
        else:
            print("\nLength calculations match ✓")

    # Return important info for debugging
    return {
        'path': path,
        'path_length': trace_length,
        'segment_lengths': segment_lengths,
        'segment_sum': computed_length,
        'objects_in_net': len(net_objs),
        'connections': len(G.edges())
    }

def visualize_multiple_paths_grid(comp_pad_pairs, json_file="Vacuum_PCB_OBjects.json", 
                                 save_path="combined_visualization.png", debug=False, 
                                 show_labels=False, grid_size=None):
    """
    Visualize multiple trace paths in a grid layout on a single figure.
    
    Args:
        comp_pad_pairs: List of tuples (comp1, pad1, comp2, pad2) for each path
        json_file: Path to the PCB JSON file
        save_path: Path to save the combined visualization
        debug: Whether to print detailed debug info
        show_labels: Whether to show labels on nodes
        grid_size: Tuple (rows, cols) for grid layout (auto-calculated if None)
        
    Returns:
        Dictionary with visualization results
    """
    # Initialize extractor and load data
    extractor = PCBTraceExtractor()
    extractor.load_json_file(json_file)
    
    # Skip empty lists
    if not comp_pad_pairs:
        print("Error: No component-pad pairs provided")
        return None
    
    # Calculate grid dimensions if not specified
    if grid_size is None:
        # Calculate a reasonable grid size based on the number of paths
        num_paths = len(comp_pad_pairs)
        cols = min(4, num_paths)  # Max 4 columns
        rows = (num_paths + cols - 1) // cols  # Ceiling division
        grid_size = (rows, cols)
    else:
        rows, cols = grid_size
    
    # Create figure with subplots
    fig_width = 5 * cols
    fig_height = 5 * rows
    fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=True)
    
    # Create subplot grid
    subfigs = fig.subfigures(rows, cols, wspace=0.07)
    
    # Handle single row or column cases where subfigs won't be a 2D array
    if rows == 1 and cols == 1:
        subfigs = np.array([[subfigs]])
    elif rows == 1:
        subfigs = subfigs.reshape(1, -1)
    elif cols == 1:
        subfigs = subfigs.reshape(-1, 1)
    
    # Track results for each path
    results = []
    
    # Process each path in its own subplot
    for i, (comp1, pad1, comp2, pad2) in enumerate(comp_pad_pairs):
        if i >= rows * cols:
            print(f"Warning: Grid too small for all paths. Skipping paths after {i}.")
            break
        
        # Get the corresponding subfigure
        row_idx = i // cols
        col_idx = i % cols
        subfig = subfigs[row_idx, col_idx]
        
        # Create axes for this subfigure
        ax = subfig.subplots()
        
        # Find the path
        trace_length = extractor.extract_traces_between_pads(comp1, pad1, comp2, pad2, debug=False)
        if trace_length is None:
            ax.text(0.5, 0.5, f"No path found\n{comp1}.{pad1} → {comp2}.{pad2}", 
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            results.append({
                'comp1': comp1, 'pad1': pad1, 
                'comp2': comp2, 'pad2': pad2,
                'success': False
            })
            continue
        
        # Find the pads
        pad_a = next((p for p in extractor.pads if p.designator==comp1 and p.pad_number==pad1), None)
        pad_b = next((p for p in extractor.pads if p.designator==comp2 and p.pad_number==pad2), None)
        
        if not pad_a or not pad_b:
            ax.text(0.5, 0.5, f"Pads not found\n{comp1}.{pad1} → {comp2}.{pad2}", 
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            results.append({
                'comp1': comp1, 'pad1': pad1, 
                'comp2': comp2, 'pad2': pad2,
                'success': False
            })
            continue
        
        # Get net objects
        net_name = pad_a.net_name
        net_objs = [o for o in extractor.objects if o.net_name == net_name]
        
        # Build graph
        G = nx.Graph()
        G.add_nodes_from(net_objs)
        
        # Add edges for connected objects
        for i, o1 in enumerate(net_objs):
            for o2 in net_objs[i+1:]:
                if o1.is_connected(o2):
                    # Calculate weight
                    if isinstance(o1, (Track, Arc)):
                        weight = o1.length * MILS_TO_MM
                    elif isinstance(o2, (Track, Arc)):
                        weight = o2.length * MILS_TO_MM
                    else:
                        weight = 0.0001
                    G.add_edge(o1, o2, weight=weight)
        
        # Find shortest path
        try:
            path = nx.shortest_path(G, pad_a, pad_b, weight='weight')
        except nx.NetworkXNoPath:
            ax.text(0.5, 0.5, f"No graph path\n{comp1}.{pad1} → {comp2}.{pad2}", 
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            results.append({
                'comp1': comp1, 'pad1': pad1, 
                'comp2': comp2, 'pad2': pad2,
                'success': False
            })
            continue
        
        # Group nodes by type
        node_groups = {
            'Pads': [n for n in G.nodes() if isinstance(n, Pad)],
            'Tracks': [n for n in G.nodes() if isinstance(n, Track)],
            'Arcs': [n for n in G.nodes() if isinstance(n, Arc)],
            'Vias': [n for n in G.nodes() if isinstance(n, Via)]
        }
        
        # Color map for nodes
        color_map = {
            'Pads': 'skyblue',
            'Tracks': 'limegreen',
            'Arcs': 'orange',
            'Vias': 'red'
        }
        
        # Node sizes (smaller than in individual plots)
        size_map = {
            'Pads': 80,
            'Tracks': 40,
            'Arcs': 60,
            'Vias': 70
        }
        
        # Create position mapping
        pos = {}
        for node in G.nodes():
            if hasattr(node, 'location'):
                pos[node] = node.location
            elif hasattr(node, 'start') and hasattr(node, 'end'):
                pos[node] = ((node.start[0] + node.end[0])/2, 
                             (node.start[1] + node.end[1])/2)
        
        # Draw nodes by type
        for node_type, nodes in node_groups.items():
            if nodes:
                sizes = [size_map[node_type] * 1.5 if n in path else size_map[node_type] for n in nodes]
                nx.draw_networkx_nodes(G, pos, ax=ax,
                                      nodelist=nodes,
                                      node_color=color_map[node_type],
                                      node_size=sizes,
                                      alpha=0.7)
        
        # Create path edges
        path_edges = list(zip(path, path[1:]))
        
        # Draw non-path edges (background)
        other_edges = [e for e in G.edges() if e not in path_edges and (e[1], e[0]) not in path_edges]
        if other_edges:
            nx.draw_networkx_edges(G, pos, ax=ax,
                                  edgelist=other_edges,
                                  edge_color='darkgray',
                                  width=0.7,
                                  alpha=0.4)
        
        # Draw path edges prominently
        nx.draw_networkx_edges(G, pos, ax=ax,
                              edgelist=path_edges,
                              edge_color='crimson',
                              width=2.0,
                              alpha=0.9)
        
        # Process segment lengths
        processed_tracks = set()
        segment_lengths = []
        computed_length = 0.0
        
        # For simplicity, we'll skip the edge labels in the grid view to avoid clutter
        
        # Highlight source and target nodes
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              nodelist=[pad_a],
                              node_color='purple',
                              node_size=120)
        
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              nodelist=[pad_b],
                              node_color='yellow',
                              node_size=120)
        
        # Add minimal labels if requested
        if show_labels:
            # Just label the source and target pads
            labels = {
                pad_a: f"{comp1}.{pad1}",
                pad_b: f"{comp2}.{pad2}"
            }
            nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=8)
        
        # Set title with path info
        subfig.suptitle(f"{comp1}.{pad1} → {comp2}.{pad2}\nLength: {trace_length:.2f} mm", fontsize=12)
        
        # Turn off axis
        ax.axis('off')
        
        # Add to results
        results.append({
            'comp1': comp1, 'pad1': pad1,
            'comp2': comp2, 'pad2': pad2,
            'success': True,
            'length': trace_length,
            'path_length': len(path)
        })
    
    # Set overall title
    fig.suptitle(f"PCB Trace Paths Visualization\n{len(comp_pad_pairs)} paths", fontsize=16)
    
    # Save the figure
    output_dir = os.path.dirname(save_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Combined visualization saved as: {save_path}")
    plt.close(fig)
    
    # Return results
    return {
        'success': True,
        'total_paths': len(comp_pad_pairs),
        'successful_paths': len([r for r in results if r.get('success', False)]),
        'save_path': save_path,
        'results': results
    }

# Simple command-line interface
if __name__ == "__main__":
    import argparse
    import numpy as np
    
    parser = argparse.ArgumentParser(description="Enhanced PCB Net Visualization with Accurate Length Labels")
    
    # Add mode selection group
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--single", action="store_true", help="Visualize a single trace path")
    mode_group.add_argument("--grid", action="store_true", help="Visualize multiple paths in a grid layout")
    mode_group.add_argument("--predefined", action="store_true", help="Use predefined test cases in a grid")
    mode_group.add_argument("--batch", action="store_true", help="Generate separate files for each predefined test case")
    
    # Add common arguments
    parser.add_argument("--json", type=str, default="Vacuum_PCB_OBjects.json", help="PCB data JSON file")
    parser.add_argument("--output", type=str, default=None, help="Output image path (default: auto-generated)")
    parser.add_argument("--output-dir", type=str, default="net_visualizations", help="Output directory for batch mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--no-labels", action="store_true", help="Disable node labels")
    
    # Add single mode arguments
    parser.add_argument("--comp1", type=str, help="First component designator (e.g., U1)")
    parser.add_argument("--pad1", type=str, help="First pad number (e.g., 20)")
    parser.add_argument("--comp2", type=str, help="Second component designator (e.g., C3)")
    parser.add_argument("--pad2", type=str, help="Second pad number (e.g., 2)")
    
    # Add grid layout options
    parser.add_argument("--rows", type=int, help="Number of rows in grid layout")
    parser.add_argument("--cols", type=int, help="Number of columns in grid layout")
    
    args = parser.parse_args()
    
    # Define predefined test cases
    predefined_cases = [
        ("U1", "11", "R66", "1"),
        ("U1", "61", "C43", "2"),
        ("U1", "20", "C3", "2"),
        ("U1", "20", "R2", "1"),
        ("U1", "9", "D5", "2"),
        ("R76", "1", "U1", "37"),
        ("U1", "4", "R54", "2"),
        ("R35", "2", "Q6", "4"),
        ("R32", "2", "Q6", "4"),
        ("U1", "22", "R17", "1"),
        ("U1", "15", "C2", "1"),
        ("U1", "19", "R15", "1"),
        ("U1", "47", "C38", "2"),
        ("U1", "6", "C26", "1"),
        ("R2", "1", "C3", "2"),
        ("U1", "9", "C21", "2"),
        ("D8", "2", "D4", "2"), 
        ("U1", "62", "C44", "1"),
        ("U1", "62", "R29", "1"),
        
    ]
    
    if args.single:
        # Check required arguments for single mode
        if not all([args.comp1, args.pad1, args.comp2, args.pad2]):
            parser.error("Single mode requires --comp1, --pad1, --comp2, and --pad2")
        
        # Generate default output path if not specified
        if not args.output:
            filename = f"{args.comp1}_{args.pad1}_to_{args.comp2}_{args.pad2}.png"
            output_dir = "net_visualizations"
            args.output = os.path.join(output_dir, filename)
        
        # Run visualization for single path
        result = visualize_net(
            comp1=args.comp1,
            pad1=args.pad1,
            comp2=args.comp2,
            pad2=args.pad2,
            json_file=args.json,
            save_path=args.output,
            debug=args.debug,
            show_labels=not args.no_labels
        )
        
        if result:
            print("\nVisualization complete!")
        else:
            print("\nVisualization failed!")
            
    elif args.grid or args.predefined:
        # Use predefined cases or exit if no cases available
        comp_pad_pairs = predefined_cases
        
        # Generate default output path if not specified
        if not args.output:
            filename = "combined_visualization.png"
            output_dir = "net_visualizations"
            args.output = os.path.join(output_dir, filename)
        
        # Determine grid size if specified
        grid_size = None
        if args.rows and args.cols:
            grid_size = (args.rows, args.cols)
        
        # Run visualization for multiple paths
        result = visualize_multiple_paths_grid(
            comp_pad_pairs=comp_pad_pairs,
            json_file=args.json,
            save_path=args.output,
            debug=args.debug,
            show_labels=not args.no_labels,
            grid_size=grid_size
        )
        
        if result:
            print(f"\nCombined visualization complete!")
            print(f"Total paths: {result['total_paths']}")
            print(f"Successful paths: {result['successful_paths']}")
            print(f"Saved to: {result['save_path']}")
        else:
            print("\nCombined visualization failed!")
    
    elif args.batch:
        # Create output directory
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            
        # Track results
        successful = 0
        failed = 0
        results = []
        
        # Initialize extractor once for all visualizations
        extractor = PCBTraceExtractor()
        extractor.load_json_file(args.json)
        print(f"Loaded PCB data from: {args.json}")
        
        print(f"\nGenerating individual visualizations for {len(predefined_cases)} test cases:")
        
        # Process each test case
        for i, (comp1, pad1, comp2, pad2) in enumerate(predefined_cases):
            print(f"\n[{i+1}/{len(predefined_cases)}] Processing: {comp1}.{pad1} → {comp2}.{pad2}")
            
            # Define output path
            output_path = os.path.join(args.output_dir, f"{comp1}_{pad1}_to_{comp2}_{pad2}.png")
            
            # Run visualization
            result = visualize_net(
                comp1=comp1,
                pad1=pad1,
                comp2=comp2,
                pad2=pad2,
                json_file=args.json, 
                save_path=output_path,
                debug=args.debug,
                show_labels=not args.no_labels
            )
            
            if result:
                successful += 1
                results.append({
                    'comp1': comp1, 'pad1': pad1,
                    'comp2': comp2, 'pad2': pad2,
                    'length': result['path_length'],
                    'file': output_path
                })
                print(f"  ✓ Success: Length = {result['path_length']:.2f} mm")
            else:
                failed += 1
                print(f"  ✗ Failed to generate visualization")
        
        # Print summary
        print(f"\nBatch processing complete!")
        print(f"Total: {len(predefined_cases)}, Successful: {successful}, Failed: {failed}")
        print(f"All visualizations saved to: {os.path.abspath(args.output_dir)}")
        
        # List all successful visualizations
        if successful > 0:
            print("\nGenerated visualizations:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r['comp1']}.{r['pad1']} → {r['comp2']}.{r['pad2']} ({r['length']:.2f} mm)")

#!/usr/bin/env python
import os
import subprocess

# List of component-pad pairs to visualize
test_cases = [
    ("U1", "11", "R66", "1"),
    ("U1", "61", "C43", "2"),
    ("U1", "20", "C3", "2"),
    ("U1", "20", "R2", "1"),
    ("U1", "9", "D5", "2"),
    ("R76", "1", "U1", "37"),
    # Add more as needed
]

output_dir = "net_visualizations"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Run each test case
for comp1, pad1, comp2, pad2 in test_cases:
    print(f"Processing: {comp1}.{pad1} → {comp2}.{pad2}")
    cmd = [
        "python", "enhanced_net_visualizer.py",
        "--comp1", comp1, "--pad1", pad1,
        "--comp2", comp2, "--pad2", pad2,
        "--debug"
    ]
    subprocess.run(cmd)

print(f"\nAll visualizations saved to: {output_dir}") 