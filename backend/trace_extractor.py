# trace_extractor.py
import json
import math
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.ops import nearest_points
from shapely.affinity import rotate, translate
# import numpy as np # Not used
from collections import defaultdict, deque
from typing import List, Dict, Optional, Any, Tuple
import matplotlib.pyplot as plt # Keep commented out unless visualizing

import plotly.graph_objects as go # Added for 3D visualization
import numpy as np # Added for potential arc calculations

# Constants for unit conversion and tolerances
MM_TO_PCB_UNITS = 1000000  # 1 mm = 1,000,000 PCB units (assuming PCB units are nm)
PCB_UNITS_TO_MM = 1 / MM_TO_PCB_UNITS # Not actually used in length calculation directly

# === Configuration Constants ===
MILS_TO_MM = 0.0254               # mils to millimeters conversion
CONNECT_TOLERANCE = 2.0           # INCREASED tolerance in mils for fuzzy endpoint matching
ARC_APPROX_SEGMENTS = 32          # resolution for approximating arcs
FALLBACK_TOLERANCE = 1.0          # fallback tolerance for second pass (currently unused)
POINT_ROUNDING_PRECISION = 2      # decimal places for rounding points (in mils) - CHANGED from 3
MAX_TRACK_WEIGHT = 0.00001        # very small weight for pad-to-track connections (in mm)
DEFAULT_WEIGHT = 0.0001           # weight for non-track connections (e.g., Pad-Via) (in mm)
# SMALL_TRACK_LENGTH = 15.0         # threshold for small tracks in mils - Unused
# SMALL_TRACK_FACTOR = 0.5          # weight factor to prioritize including small tracks - Unused


class NetObject:
    """
    Base class for PCB net objects.
    """
    def __init__(self, net_name: str):
        self.net_name = net_name
        self.length = 0.0 # Ensure all subclasses have a length attribute (even if 0)

    def get_geometry(self):
        raise NotImplementedError

    def get_layers(self) -> set:
        raise NotImplementedError

    def endpoints(self) -> list[tuple]:
        """Connection points: for tracks/arcs their ends; for pads/vias their centers."""
        return []

    def is_same_net(self, other: "NetObject") -> bool:
        return self.net_name == other.net_name

    def is_connected(self, other: "NetObject", tolerance=None) -> bool:
        if tolerance is None:
            tolerance = CONNECT_TOLERANCE # Use the class constant

        if not self.is_same_net(other):
            return False

        layers1 = self.get_layers()
        layers2 = other.get_layers()
        # Allow connection if layers overlap or one is 'ALL' (Pad/Via)
        if "ALL" not in layers1 and "ALL" not in layers2 and layers1.isdisjoint(layers2):
            return False

        # Check 1: Endpoint-to-endpoint proximity check
        for p1 in self.endpoints():
            for p2 in other.endpoints():
                if math.hypot(p1[0]-p2[0], p1[1]-p2[1]) <= tolerance:
                    return True

        # Check 2: Buffered geometry intersection check (more robust for pads/vias)
        try:
            # Use a small buffer just to account for floating point noise if needed,
            # or slightly larger if relying on it more. Let's use tolerance/10.
            geom_tolerance = tolerance * 0.1 # Smaller buffer for geometry intersection
            # Ensure get_geometry returns something valid before buffering
            geom1_base = self.get_geometry()
            geom2_base = other.get_geometry()
            if geom1_base is None or geom2_base is None:
                return False # Cannot check intersection if geometry is missing

            geom1 = geom1_base.buffer(geom_tolerance)
            geom2 = geom2_base.buffer(geom_tolerance)
            if geom1.intersects(geom2):
                 # Check if they are on compatible layers again before confirming intersection
                 if "ALL" in layers1 or "ALL" in layers2 or not layers1.isdisjoint(layers2):
                     return True
        except Exception as e:
             # Handle potential shapely errors gracefully
             # print(f"Warning: Shapely error during intersection check: {e}") # Optional debug print
             pass # Should log this ideally

        return False

class Pad(NetObject):
    """
    Component pad; rectangular or circular. Connection at center only.
    """
    def __init__(self, designator: str, pad_number: str, net_name: str,
                 location: tuple, layer: int,
                 width: float, height: float,
                 hole_size: float = 0.0,
                 rotation: float = 0.0,
                 shape: str = "Rectangular"):
        super().__init__(net_name)
        self.designator = designator
        self.pad_number = pad_number
        self.location = location # Stored in mils
        self.layer = layer
        self.width = width
        self.height = height
        self.hole_size = hole_size
        self.rotation = rotation
        self.shape = shape
        # self.length = 0.0 # Set in base class

    def get_geometry(self):
        # Geometry for intersection checks, centered at origin then translated
        w2, h2 = self.width / 2.0, self.height / 2.0
        if self.hole_size > 0: # Through-hole approximation
             # Use max(width, height) for effective radius? Or just hole size?
             radius = max(w2, h2, self.hole_size / 2.0)
             if radius <= 0: return Point(0,0) # Avoid buffering Point(0,0) by 0
             geom = Point(0, 0).buffer(radius)
        elif self.shape.lower().startswith("round") or self.shape.lower() == "circle" or self.shape.lower() == "oval":
            radius = self.width / 2.0 # Assume width=height for circle/round, width for oval
            if radius <= 0: return Point(0,0)
            geom = Point(0, 0).buffer(radius)
        else: # Rectangular (default)
            coords = [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2), (-w2, -h2)]
            try:
                geom = Polygon(coords)
            except Exception: # Handle degenerate polygons if width/height are zero
                 return Point(0,0)
            if abs(self.rotation) > 1e-6:
                 shapely_rotation = -self.rotation
                 geom = rotate(geom, shapely_rotation, origin=(0, 0), use_radians=False)

        # Translate to actual location
        return translate(geom, xoff=self.location[0], yoff=self.location[1])


    def endpoints(self) -> list[tuple]:
        return [self.location]

    def get_layers(self) -> set:
        return {"ALL"} if self.hole_size > 0 else {self.layer}

    def __str__(self):
        return f"Pad({self.designator}.{self.pad_number}, net={self.net_name})"

    def __hash__(self):
        return hash((self.designator, self.pad_number))
    def __eq__(self, other):
        if not isinstance(other, Pad):
            return NotImplemented
        return self.designator == other.designator and self.pad_number == other.pad_number

class Track(NetObject):
    """Straight copper segment."""
    def __init__(self, start: tuple, end: tuple, net_name: str,
                 layer: int, length: float):
        super().__init__(net_name)
        self.start = start # mils
        self.end = end     # mils
        self.layer = layer
        self.length = length # mils

    def get_geometry(self):
        # Avoid creating LineString with identical points
        if self.start == self.end:
            return Point(self.start)
        return LineString([self.start, self.end])

    def endpoints(self) -> list[tuple]:
        return [self.start, self.end]

    def get_layers(self) -> set:
        return {self.layer}

    def __str__(self):
        # Use a more unique identifier if possible, maybe based on rounded coords?
        p1 = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.start)
        p2 = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.end)
        return f"Track({p1}-{p2}, L={self.length:.2f}mils)"

    def __hash__(self):
        p1 = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.start)
        p2 = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.end)
        if p1 > p2: p1, p2 = p2, p1
        return hash(("Track", p1, p2, self.layer, self.net_name))
    def __eq__(self, other):
        if not isinstance(other, Track): return NotImplemented
        p1_self = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.start)
        p2_self = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.end)
        if p1_self > p2_self: p1_self, p2_self = p2_self, p1_self

        p1_other = tuple(round(c, POINT_ROUNDING_PRECISION) for c in other.start)
        p2_other = tuple(round(c, POINT_ROUNDING_PRECISION) for c in other.end)
        if p1_other > p2_other: p1_other, p2_other = p2_other, p1_other

        return (p1_self == p1_other and
                p2_self == p2_other and
                self.layer == other.layer and
                self.net_name == other.net_name)


class Arc(NetObject):
    """Curved copper segment approximated as a polyline."""
    def __init__(self, center: tuple, radius: float,
                 start_angle: float, end_angle: float,
                 start: tuple, end: tuple, # Precise start/end points
                 net_name: str, layer: int, length: float):
        super().__init__(net_name)
        self.center = center # mils
        self.radius = radius # mils
        self.start_angle_deg = start_angle
        self.end_angle_deg = end_angle
        # Convert angles to radians for math functions
        self.start_angle_rad = math.radians(start_angle)
        self.end_angle_rad = math.radians(end_angle)
        # Store precise start/end points from JSON
        self.start = start # mils
        self.end = end     # mils
        self.layer = layer
        self.length = length # mils

        # Ensure angle range logic handles wrap-around if needed (e.g., end < start)
        # For simplicity assume end_angle_deg is always "after" start_angle_deg in CCW direction
        delta_angle = self.end_angle_rad - self.start_angle_rad
        # Handle potential wrap-around if not already handled by source data
        if delta_angle < 0:
             delta_angle += 2 * math.pi

        self.delta_angle_rad = delta_angle


    def get_geometry(self):
        if self.radius <= 0 or self.delta_angle_rad <= 1e-6:
             # Handle degenerate arcs (e.g., zero radius or angle)
             return LineString([self.start, self.end]) # Approximate as straight line

        # Generate points along the arc
        num_segments = ARC_APPROX_SEGMENTS
        pts = []
        for i in range(num_segments + 1):
            angle = self.start_angle_rad + self.delta_angle_rad * i / num_segments
            x = self.center[0] + self.radius * math.cos(angle)
            y = self.center[1] + self.radius * math.sin(angle)
            pts.append((x, y))

        # Replace calculated start/end with precise points from JSON
        # This accounts for cases where the geometric calculation might differ slightly
        # due to floating point precision or how the source tool defines arcs.
        pts[0] = self.start
        pts[-1] = self.end

        # Avoid creating LineString with identical points if start/end somehow collapsed
        if len(pts) > 1 and pts[0] == pts[-1]:
            return Point(pts[0])
        elif len(pts) < 2:
             return Point(self.start) # Should not happen with num_segments > 0

        return LineString(pts)

    def endpoints(self) -> list[tuple]:
        return [self.start, self.end]

    def get_layers(self) -> set:
        return {self.layer}

    def __str__(self):
        return f"Arc(C={self.center}, R={self.radius:.2f}, L={self.length:.2f}mils)"

    def __hash__(self):
         # Hash based on rounded center, radius, angles, layer, netname
         # Rounding angles might be tricky, use precise start/end points instead?
         p1 = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.start)
         p2 = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.end)
         if p1 > p2: p1, p2 = p2, p1
         center_r = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.center)
         radius_r = round(self.radius, POINT_ROUNDING_PRECISION)
         # Use start/end points and center/radius for more reliable hashing than angles
         return hash(("Arc", p1, p2, center_r, radius_r, self.layer, self.net_name))

    def __eq__(self, other):
         if not isinstance(other, Arc): return NotImplemented
         # Compare based on key attributes, primarily rounded endpoints and geometry params
         p1_self = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.start)
         p2_self = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.end)
         if p1_self > p2_self: p1_self, p2_self = p2_self, p1_self

         p1_other = tuple(round(c, POINT_ROUNDING_PRECISION) for c in other.start)
         p2_other = tuple(round(c, POINT_ROUNDING_PRECISION) for c in other.end)
         if p1_other > p2_other: p1_other, p2_other = p2_other, p1_other

         center_self_r = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.center)
         center_other_r = tuple(round(c, POINT_ROUNDING_PRECISION) for c in other.center)
         radius_self_r = round(self.radius, POINT_ROUNDING_PRECISION)
         radius_other_r = round(other.radius, POINT_ROUNDING_PRECISION)

         return (p1_self == p1_other and
                 p2_self == p2_other and
                 center_self_r == center_other_r and
                 abs(radius_self_r - radius_other_r) < 1e-3 and # Tolerance for radius
                 self.layer == other.layer and
                 self.net_name == other.net_name)


class Via(NetObject):
    """Drilled inter-layer connection."""
    def __init__(self, location: tuple, net_name: str,
                 from_layer: int, to_layer: int, hole_size: float):
        super().__init__(net_name)
        self.location = location # mils
        self.from_layer = from_layer
        self.to_layer = to_layer
        self.hole_size = hole_size # mils
        # self.length = 0.0 # Set in base class (Vias usually have negligible length for trace calculations)

    def get_geometry(self):
        # Vias are typically circular
        radius = self.hole_size / 2.0
        if radius <= 0: return Point(self.location) # Handle zero hole size
        return Point(*self.location).buffer(radius)

    def endpoints(self) -> list[tuple]:
         # Connection point is the center
        return [self.location]

    def get_layers(self) -> set:
         # Vias connect things across layers, so treat as connecting on 'ALL' layers
         # for the purpose of graph connectivity check.
        return {"ALL"}

    def __str__(self):
        return f"Via(loc={self.location}, net={self.net_name})"

    def __hash__(self):
        loc_r = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.location)
        return hash(("Via", loc_r, self.net_name))

    def __eq__(self, other):
        if not isinstance(other, Via): return NotImplemented
        loc_self_r = tuple(round(c, POINT_ROUNDING_PRECISION) for c in self.location)
        loc_other_r = tuple(round(c, POINT_ROUNDING_PRECISION) for c in other.location)
        # Consider vias equal if location and net match
        return (loc_self_r == loc_other_r and
                self.net_name == other.net_name)

class PCBTraceExtractor:
    """
    Extracts and analyzes PCB traces from JSON data.
    """
    def __init__(self, pcb_data: dict = None):
        print(f"PCBTraceExtractor initialized with pcb_data of type: {type(pcb_data)}")
        if pcb_data:
            print(f"PCB data keys: {pcb_data.keys()}")
            print(f"Components length: {len(pcb_data.get('components', []))}")
            
        self.pcb_data = pcb_data
        self.objects = []
        self.pads = []
        self.pad_cache = {}  # Cache for pad lookups by designation and pad number
        self.connection_cache = {}  # Cache for connection results
        
        if pcb_data:
            self._process_pcb_data()
    
    def _process_pcb_data(self):
        """Process the PCB data and build internal data structures."""
        if not self.pcb_data:
            return
            
        # Clear any existing data
        self.objects = []
        self.pads = []
        self.pad_cache = {}
        self.connection_cache = {}
        
        # Process components and their pads
        for comp in self.pcb_data.get('components', []):
            d = comp['designator']
            # Use component layer if pad doesn't specify, default to 1 if neither specifies
            comp_layer = comp.get('layer', 1)
            for p in comp.get('pads', []):
                pad_layer = p.get('layer', comp_layer)  # Pad layer overrides component layer
                pad = Pad(
                    designator=d,
                    pad_number=str(p['padNumber']),
                    net_name=p['netName'],
                    location=(p['location']['x'], p['location']['y']),  # Assume mils
                    layer=pad_layer,
                    width=p.get('width', 0),
                    height=p.get('height', 0),
                    hole_size=p.get('holeSize', 0),
                    rotation=p.get('rotation', 0),
                    shape=p.get('shape', 'Rectangular')  # Default shape
                )
                # Only add pads with net names
                if pad.net_name:
                    self.objects.append(pad)
                    self.pads.append(pad)
                    self.pad_cache[(d, str(p['padNumber']))] = pad
        
        # Process tracks
        for t in self.pcb_data.get('tracks', []):
            track = Track(
                start=(t['start']['x'], t['start']['y']),  # Assume mils
                end=(t['end']['x'], t['end']['y']),        # Assume mils
                net_name=t['netName'],
                layer=t['layer'],
                length=t['length']  # Assume mils
            )
            # Only add tracks with net names and non-zero length
            if track.net_name and track.length > 1e-6:
                self.objects.append(track)
        
        # Process arcs
        for a in self.pcb_data.get('arcs', []):
            arc = Arc(
                center=(a['center']['x'], a['center']['y']),  # Assume mils
                radius=a['radius'],                           # Assume mils
                start_angle=a['startAngle'],                  # Assume degrees
                end_angle=a['endAngle'],                      # Assume degrees
                start=(a['start']['x'], a['start']['y']),     # Assume mils
                end=(a['end']['x'], a['end']['y']),           # Assume mils
                net_name=a['netName'],
                layer=a['layer'],
                length=a['length']  # Assume mils
            )
            # Only add arcs with net names and non-zero length
            if arc.net_name and arc.length > 1e-6:
                self.objects.append(arc)
        
        # Process vias
        for v in self.pcb_data.get('vias', []):
            via = Via(
                location=(v['location']['x'], v['location']['y']),  # Assume mils
                net_name=v['netName'],
                from_layer=v['fromLayer'],
                to_layer=v['toLayer'],
                hole_size=v.get('holeSize', 0)  # Assume mils
            )
            # Only add vias with net names
            if via.net_name:
                self.objects.append(via)
        
        print(f"Loaded {len(self.objects)} objects ({len(self.pads)} pads).")  # Debug print
    
    def get_nets(self) -> List[dict]:
        """Get a list of all nets in the PCB with their component and pad counts."""
        if not self.pcb_data:
            return []
            
        net_info = defaultdict(lambda: {'component_count': 0, 'pad_count': 0})
        components = set()
        
        # Count components and pads per net
        for comp in self.pcb_data.get('components', []):
            for pad in comp.get('pads', []):
                net_name = pad.get('netName', '')
                if net_name:
                    net_info[net_name]['pad_count'] += 1
                    if comp['designator'] not in components:
                        net_info[net_name]['component_count'] += 1
                        components.add(comp['designator'])
        
        # Convert to list of dictionaries
        return [{'net_name': net, **info} for net, info in net_info.items()]
    
    def calculate_trace_lengths(self, net_name: str) -> List[dict]:
        """Calculate trace lengths between all pads in a net."""
        if not self.pcb_data:
            return []
            
        # Get all pads for this net
        net_pads = []
        for comp in self.pcb_data.get('components', []):
            for pad in comp.get('pads', []):
                if pad['netName'] == net_name:
                    net_pads.append({
                        'component': comp['designator'],
                        'pad': pad['padNumber'],
                        'x': pad['location']['x'],
                        'y': pad['location']['y']
                    })
        
        # Calculate lengths between all pad pairs
        trace_lengths = []
        for i, pad1 in enumerate(net_pads):
            for pad2 in net_pads[i+1:]:
                length = self.extract_traces_between_pads(
                    pad1['component'], pad1['pad'],
                    pad2['component'], pad2['pad']
                )
                if length is not None:
                    trace_lengths.append({
                        'start_component': pad1['component'],
                        'start_pad': pad1['pad'],
                        'end_component': pad2['component'],
                        'end_pad': pad2['pad'],
                        'length_mm': length * MILS_TO_MM  # Convert to mm
                    })
        
        return trace_lengths

    def round_point(self, point):
        """Round a point tuple to a specified precision for hashing/comparison"""
        # Ensure point is a tuple of numbers
        if not isinstance(point, tuple) or len(point) != 2:
            # print(f"Warning: Invalid point format for rounding: {point}") # Debug
            return None # Or raise error
        try:
            return (round(point[0], POINT_ROUNDING_PRECISION), round(point[1], POINT_ROUNDING_PRECISION))
        except TypeError:
             # print(f"Warning: Could not round point: {point}") # Debug
             return None # Or raise error

    def build_point_to_objects_map(self, net_objs):
        """Build a mapping of rounded points to the list of objects connected at that point."""
        point_to_objs = defaultdict(list)
        for obj in net_objs:
            for point in obj.endpoints():
                point_rounded = self.round_point(point)
                if point_rounded is not None:
                    # Avoid adding duplicates of the same object instance for a single point
                    if obj not in point_to_objs[point_rounded]:
                        point_to_objs[point_rounded].append(obj)
        return point_to_objs

    def build_accurate_graph(self, net_objs, pad_a, pad_b):
        """Build graph connecting objects sharing exactly rounded endpoints."""
        G = nx.Graph()
        # Add all objects as nodes initially
        G.add_nodes_from(net_objs)

        point_to_objs = self.build_point_to_objects_map(net_objs)

        # Add edges between objects that share an exact rounded endpoint
        for point, objs_at_point in point_to_objs.items():
            # Connect all pairs of objects at this point
            for i in range(len(objs_at_point)):
                for j in range(i + 1, len(objs_at_point)):
                    obj1 = objs_at_point[i]
                    obj2 = objs_at_point[j]

                    # Determine edge weight based on object types
                    weight = DEFAULT_WEIGHT # Default for Pad-Pad, Via-Via, Pad-Via
                    # If one is a Track/Arc, use its length (converted to mm)
                    # Prioritize using track/arc length for weight calculation
                    if isinstance(obj1, (Track, Arc)):
                        weight = max(obj1.length * MILS_TO_MM, MAX_TRACK_WEIGHT) # Ensure non-zero for pathfinding
                    elif isinstance(obj2, (Track, Arc)):
                        weight = max(obj2.length * MILS_TO_MM, MAX_TRACK_WEIGHT) # Ensure non-zero for pathfinding

                    # Special low weight for Pad-to-Track/Arc to encourage entry/exit via pads
                    if (isinstance(obj1, Pad) and isinstance(obj2, (Track, Arc))) or \
                       (isinstance(obj2, Pad) and isinstance(obj1, (Track, Arc))):
                       weight = MAX_TRACK_WEIGHT

                    # Add the edge if not already present
                    if not G.has_edge(obj1, obj2):
                         G.add_edge(obj1, obj2, weight=weight)
                         # print(f"AccurateGraph: Added edge {obj1} -- {obj2} (weight {weight:.6f}) at point {point}") # Debug


        # Ensure target pads are in the graph (they should be from add_nodes_from)
        if pad_a not in G: G.add_node(pad_a)
        if pad_b not in G: G.add_node(pad_b)

        return G

    def build_fallback_graph(self, net_objs, pad_a=None, pad_b=None):
        """Build a more permissive graph using is_connected with tolerance."""
        G = nx.Graph()
        G.add_nodes_from(net_objs)

        # Use provided tolerance or default
        tolerance = FALLBACK_TOLERANCE if FALLBACK_TOLERANCE is not None else CONNECT_TOLERANCE

        for i, o1 in enumerate(net_objs):
            for o2 in net_objs[i+1:]:
                # Check connectivity using the specified tolerance
                if o1.is_connected(o2, tolerance=tolerance):
                    # Use average length (in mm) for weight, ensure minimum weight
                    weight = ((o1.length + o2.length) / 2) * MILS_TO_MM
                    weight = max(weight, DEFAULT_WEIGHT) # Ensure non-zero weight

                    # Special low weight for Pad-to-Track/Arc
                    if (isinstance(o1, Pad) and isinstance(o2, (Track, Arc))) or \
                       (isinstance(o2, Pad) and isinstance(o1, (Track, Arc))):
                       weight = MAX_TRACK_WEIGHT

                    if not G.has_edge(o1, o2):
                        G.add_edge(o1, o2, weight=weight)
                        # print(f"FallbackGraph: Added edge {o1} -- {o2} (weight {weight:.6f})") # Debug

        # Ensure target pads are in the graph
        if pad_a not in G: G.add_node(pad_a)
        if pad_b not in G: G.add_node(pad_b)

        return G

    def build_bidirectional_graph(self, net_objs, pad_a, pad_b):
         """Builds a graph using is_connected and specific weighting."""
         G = nx.Graph()
         G.add_nodes_from(net_objs)

         # Connect objects using is_connected (which uses CONNECT_TOLERANCE)
         for i, o1 in enumerate(net_objs):
             for o2 in net_objs[i+1:]:
                 if o1.is_connected(o2): # Uses default CONNECT_TOLERANCE
                     # Determine edge weight
                     weight = DEFAULT_WEIGHT # Default (e.g., Pad-Pad, Pad-Via)

                     # If connection involves a track/arc, use its length
                     if isinstance(o1, (Track, Arc)):
                         weight = max(o1.length * MILS_TO_MM, MAX_TRACK_WEIGHT)
                     elif isinstance(o2, (Track, Arc)):
                         weight = max(o2.length * MILS_TO_MM, MAX_TRACK_WEIGHT)

                     # Special very low weight for Pad-to-Track/Arc connections
                     if (isinstance(o1, Pad) and isinstance(o2, (Track, Arc))) or \
                        (isinstance(o2, Pad) and isinstance(o1, (Track, Arc))):
                         weight = MAX_TRACK_WEIGHT

                     if not G.has_edge(o1, o2):
                          G.add_edge(o1, o2, weight=weight)
                          # print(f"BidirectionalGraph: Added edge {o1} -- {o2} (weight {weight:.6f})") # Debug

         # Explicitly add the start/end pads if they somehow got missed
         if pad_a not in G: G.add_node(pad_a)
         if pad_b not in G: G.add_node(pad_b)

         return G


    def calculate_path_length(self, path):
        """Calculate total length of tracks and arcs in a path"""
        # Filter out non-Track/Arc objects (like Pads, Vias) from the path
        tracks_in_path = [o for o in path if isinstance(o, (Track, Arc))]
        # Sum the length attribute (stored in mils) and convert to mm
        total_length_mils = sum(t.length for t in tracks_in_path)
        return total_length_mils * MILS_TO_MM

    def extract_traces_between_pads(self, c1: str, p1: str, c2: str, p2: str, debug: bool=False) -> float | None:
        """
        Extract trace length between two pads using a robust algorithm with multiple fallback mechanisms.
        Returns the trace length in mm or None if no path is found.
        """
        # Create a unique key for caching, order doesn't matter
        key_part1 = (c1, p1)
        key_part2 = (c2, p2)
        cache_key = tuple(sorted((key_part1, key_part2)))

        if cache_key in self.connection_cache:
            # print(f"Cache hit for {cache_key}") # Debug
            return self.connection_cache[cache_key]

        # Locate pads - use cache for faster lookup
        pad_a = self.pad_cache.get((c1, p1))
        pad_b = self.pad_cache.get((c2, p2))

        # If not in cache, find them (this should ideally only happen once per pad)
        if not pad_a:
            pad_a = next((pad for pad in self.pads if pad.designator==c1 and pad.pad_number==p1), None)
            if pad_a: self.pad_cache[(c1, p1)] = pad_a
        if not pad_b:
            pad_b = next((pad for pad in self.pads if pad.designator==c2 and pad.pad_number==p2), None)
            if pad_b: self.pad_cache[(c2, p2)] = pad_b

        if not pad_a or not pad_b:
            if debug: print(f"Error: Could not find one or both pads: {c1}.{p1}, {c2}.{p2}")
            self.connection_cache[cache_key] = None # Cache failure
            return None

        if pad_a.net_name != pad_b.net_name:
            if debug: print(f"Error: Pads are on different nets: {pad_a.net_name} vs {pad_b.net_name}")
            self.connection_cache[cache_key] = None # Cache failure
            return None

        # Filter objects belonging to the target net
        net_objs = [o for o in self.objects if o.net_name == pad_a.net_name]
        if pad_a not in net_objs: net_objs.append(pad_a) # Ensure pads are included if filtered out previously
        if pad_b not in net_objs: net_objs.append(pad_b)

        if debug: print(f"\nProcessing {c1}.{p1} <-> {c2}.{p2} on net {pad_a.net_name} ({len(net_objs)} objects)")

        # Try different graph building strategies
        # build_accurate_graph relies on exact endpoint matches (after rounding)
        # build_bidirectional_graph uses is_connected (tolerance based)
        # build_fallback_graph uses a larger tolerance (if needed)
        strategies = [
            self.build_accurate_graph,
            self.build_bidirectional_graph,
            # self.build_fallback_graph # Keep fallback commented unless needed
        ]

        shortest_length = None
        best_path = None
        strategy_used = "None"

        for strategy_func in strategies:
            strategy_name = strategy_func.__name__
            if debug: print(f"Trying strategy: {strategy_name}")
            G = strategy_func(net_objs, pad_a, pad_b)

            # Verify pads exist in the graph built by the strategy
            if pad_a not in G or pad_b not in G:
                 if debug: print(f"Strategy {strategy_name} failed: Start or end pad not in graph.")
                 continue

            try:
                # Use Dijkstra's algorithm to find the shortest path based on 'weight'
                path = nx.shortest_path(G, source=pad_a, target=pad_b, weight='weight')

                # Calculate the length of this path based on actual track/arc lengths
                current_length = self.calculate_path_length(path)

                if debug:
                    print(f"Path found using {strategy_name} ({len(path)} nodes): Length = {current_length:.5f} mm")
                    # Enhanced path printing (print each item on its own line):
                    print("Full Path Details:")
                    for i, obj in enumerate(path):
                        # Use the standard __str__ representation which is already quite informative
                        # For Pads, it includes designator.pad_number
                        print(f"  {i+1}. {str(obj)}") # Print each object directly

                # Store the first valid path found as the potential result
                # Subsequent strategies might find paths if earlier ones fail,
                # but the 'accurate' one is preferred if it works.
                if shortest_length is None: # Or potentially check if this path is significantly better?
                    shortest_length = current_length
                    best_path = path
                    strategy_used = strategy_name
                    # We can break here if the accurate strategy works, as it's preferred.
                    if strategy_func == self.build_accurate_graph:
                        break


            except nx.NetworkXNoPath:
                if debug: print(f"No path found using {strategy_name}.")
                continue
            except nx.NodeNotFound as e:
                 if debug: print(f"Strategy {strategy_name} failed: Node not found in graph - {e}")
                 continue

        # Store the best path in a separate cache for retrieve_path_details
        if best_path is not None:
            self.path_cache = getattr(self, 'path_cache', {})
            self.path_cache[cache_key] = (best_path, strategy_used)

        # Cache the result (even if None)
        self.connection_cache[cache_key] = shortest_length

        if shortest_length is not None:
            if debug: print(f"Final Result: Length={shortest_length:.5f} mm using {strategy_used}")
            return shortest_length
        else:
            if debug: print(f"No path found between {c1}.{p1} and {c2}.{p2} using any strategy.")
            return None
            
    def get_trace_path(self, c1: str, p1: str, c2: str, p2: str) -> dict:
        """
        Retrieve the detailed path information for a trace between two pads.
        First tries to get cached path, if not available, runs extract_traces_between_pads.
        
        Returns:
            dict: Path information with the following keys:
                - path_exists (bool): True if a path was found
                - length_mm (float): Total length of the path in mm
                - path_description (str): Text description of the path
                - path_elements (list): Detailed objects along the path
        """
        # Create a unique key for caching, order doesn't matter
        key_part1 = (c1, p1)
        key_part2 = (c2, p2)
        cache_key = tuple(sorted((key_part1, key_part2)))
        
        # Initialize result
        result = {
            'path_exists': False,
            'length_mm': None,
            'path_description': None,
            'path_elements': None
        }
        
        # Check if we have a cached path
        path_cache = getattr(self, 'path_cache', {})
        if cache_key in path_cache:
            best_path, strategy_used = path_cache[cache_key]
        else:
            # If no cached path, try to calculate it (will also cache the result)
            length = self.extract_traces_between_pads(c1, p1, c2, p2)
            if length is None:
                return result  # No path found
                
            # Try to get the newly cached path
            if cache_key in getattr(self, 'path_cache', {}):
                best_path, strategy_used = self.path_cache[cache_key]
            else:
                # This should not happen unless extract_traces_between_pads was modified
                return {
                    'path_exists': True,
                    'length_mm': length,
                    'path_description': f"Path from {c1}.{p1} to {c2}.{p2}, length: {length:.5f} mm",
                    'path_elements': None
                }
        
        # We have a path, now extract the detailed elements
        length_mm = self.calculate_path_length(best_path) if best_path else None
        
        if best_path and length_mm is not None:
            # Create a description
            path_description = f"Path from {c1}.{p1} to {c2}.{p2} ({len(best_path)} elements, {length_mm:.5f} mm)"
            
            # Build detailed path elements
            path_elements = []
            for i, obj in enumerate(best_path):
                element = {
                    'index': i,
                    'type': obj.__class__.__name__
                }
                
                # Add type-specific details
                if isinstance(obj, Pad):
                    element.update({
                        'component': obj.designator,
                        'pad': obj.pad_number,
                        'location': obj.location,
                        'layer': obj.layer,
                        'net': obj.net_name
                    })
                elif isinstance(obj, Track):
                    element.update({
                        'start': obj.start,
                        'end': obj.end,
                        'layer': obj.layer,
                        'net': obj.net_name,
                        'length': obj.length  # mils
                    })
                elif isinstance(obj, Arc):
                    element.update({
                        'center': obj.center,
                        'radius': obj.radius,
                        'start': obj.start,
                        'end': obj.end,
                        'start_angle': obj.start_angle_deg,
                        'end_angle': obj.end_angle_deg,
                        'layer': obj.layer,
                        'net': obj.net_name,
                        'length': obj.length  # mils
                    })
                elif isinstance(obj, Via):
                    element.update({
                        'location': obj.location,
                        'from_layer': obj.from_layer,
                        'to_layer': obj.to_layer,
                        'net': obj.net_name
                    })
                
                path_elements.append(element)
            
            return {
                'path_exists': True,
                'length_mm': length_mm,
                'path_description': path_description,
                'path_elements': path_elements,
                'strategy_used': strategy_used
            }
        
        return result

    def extract_traces(self, component1, pad1, component2, pad2):
        """Compatibility method"""
        return self.extract_traces_between_pads(component1, pad1, component2, pad2)

    def get_trace_details(self, net_name: str) -> dict:
        """Get detailed information about all traces in a net."""
        if not self.pcb_data:
            return {}
            
        # Get all pads for this net
        net_pads = []
        for comp in self.pcb_data.get('components', []):
            for pad in comp.get('pads', []):
                if pad.get('netName') == net_name:
                    net_pads.append({
                        'component': comp['designator'],
                        'pad': str(pad['padNumber']),
                        'x': pad['location']['x'],
                        'y': pad['location']['y'],
                        'layer': pad.get('layer', comp.get('layer', 1))
                    })
        
        # Get all tracks and arcs for this net
        net_segments = []
        for track in self.pcb_data.get('tracks', []):
            if track.get('netName') == net_name:
                net_segments.append({
                    'type': 'track',
                    'start': {'x': track['start']['x'], 'y': track['start']['y']},
                    'end': {'x': track['end']['x'], 'y': track['end']['y']},
                    'layer': track['layer'],
                    'length': track['length']
                })
        
        for arc in self.pcb_data.get('arcs', []):
            if arc.get('netName') == net_name:
                net_segments.append({
                    'type': 'arc',
                    'center': {'x': arc['center']['x'], 'y': arc['center']['y']},
                    'radius': arc['radius'],
                    'start_angle': arc['startAngle'],
                    'end_angle': arc['endAngle'],
                    'start': {'x': arc['start']['x'], 'y': arc['start']['y']},
                    'end': {'x': arc['end']['x'], 'y': arc['end']['y']},
                    'layer': arc['layer'],
                    'length': arc['length']
                })
        
        # Get all vias for this net
        net_vias = []
        for via in self.pcb_data.get('vias', []):
            if via.get('netName') == net_name:
                net_vias.append({
                    'x': via['location']['x'],
                    'y': via['location']['y'],
                    'from_layer': via['fromLayer'],
                    'to_layer': via['toLayer'],
                    'hole_size': via.get('holeSize', 0)
                })
        
        # Try to get connection information for this net
        connection_info = None
        if len(net_pads) >= 2:
            # Pick the first two pads to calculate a default path
            pad1 = net_pads[0]
            pad2 = net_pads[1]
            
            length = self.extract_traces_between_pads(
                pad1['component'], pad1['pad'],
                pad2['component'], pad2['pad']
            )
            
            if length is not None:
                connection_info = {
                    'start_component': pad1['component'],
                    'start_pad': pad1['pad'],
                    'end_component': pad2['component'],
                    'end_pad': pad2['pad'],
                    'length_mm': length  # Already in mm from extract_traces_between_pads
                }
        
        return {
            'net_name': net_name,
            'pads': net_pads,
            'segments': net_segments,
            'vias': net_vias,
            'connection_info': connection_info
        }
    
    def get_critical_paths(self, net_name: str) -> List[dict]:
        """Analyze critical paths in a net."""
        if not self.pcb_data:
            return []
            
        # Get all pads for this net
        net_pads = []
        for comp in self.pcb_data.get('components', []):
            for pad in comp.get('pads', []):
                if pad.get('netName') == net_name:
                    net_pads.append({
                        'component': comp['designator'],
                        'pad': str(pad['padNumber']),
                        'x': pad['location']['x'],
                        'y': pad['location']['y']
                    })
        
        # Calculate all possible paths between pads
        paths = []
        for i, pad1 in enumerate(net_pads):
            for pad2 in net_pads[i+1:]:
                length = self.extract_traces_between_pads(
                    pad1['component'], pad1['pad'],
                    pad2['component'], pad2['pad']
                )
                if length is not None:
                    paths.append({
                        'start_component': pad1['component'],
                        'start_pad': pad1['pad'],
                        'end_component': pad2['component'],
                        'end_pad': pad2['pad'],
                        'length_mm': length  # Already in mm from extract_traces_between_pads
                    })
        
        # Sort paths by length
        paths.sort(key=lambda x: x['length_mm'], reverse=True)
        
        return {
            'net_name': net_name,
            'paths': paths,
            'longest_path': paths[0] if paths else None,
            'total_length_mm': sum(p['length_mm'] for p in paths)
        }
    
    def visualize_net(self, net_name: str, output_path: str = None):
        """Visualize a net's traces and components using Matplotlib (2D)."""
        from matplotlib.patches import Circle, Rectangle, Arc as MplArc # Local import is fine
        
        # Get net details
        net_details = self.get_trace_details(net_name)
        if not net_details:
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Plot pads
        for pad in net_details['pads']:
            circle = Circle((pad['x'], pad['y']), 5, color='red', alpha=0.5)
            ax.add_patch(circle)
            ax.text(pad['x'], pad['y'], f"{pad['component']}.{pad['pad']}", 
                   fontsize=8, ha='center', va='center')
        
        # Plot tracks and arcs
        for segment in net_details['segments']:
            if segment['type'] == 'track':
                ax.plot([segment['start']['x'], segment['end']['x']],
                       [segment['start']['y'], segment['end']['y']],
                       'b-', linewidth=1)
            else:  # arc
                arc = MplArc((segment['center']['x'], segment['center']['y']),
                           2 * segment['radius'], 2 * segment['radius'],
                           theta1=segment['start_angle'],
                           theta2=segment['end_angle'],
                           color='blue', linewidth=1)
                ax.add_patch(arc)
        
        # Plot vias
        for via in net_details['vias']:
            circle = Circle((via['x'], via['y']), 3, color='green', alpha=0.5)
            ax.add_patch(circle)
        
        # Set equal aspect ratio and remove axes
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Add title
        ax.set_title(f"Net: {net_name}")
        
        # Save or show
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
        
        return fig

    def _get_color_for_net(self, net_name: str) -> str:
        """
        Generate a consistent color for a given net name.
        
        Args:
            net_name: The name of the net
            
        Returns:
            A hex color string
        """
        # Common net names get fixed colors
        common_nets = {
            'GND': '#1a1a1a',       # Dark gray/black
            'VCC': '#ff0000',       # Red
            'VDD': '#ff3333',       # Lighter red
            'VBUS': '#ff6600',      # Orange
            'VSS': '#404040',       # Dark gray
            '3V3': '#cc33ff',       # Purple
            '5V': '#9900cc',        # Dark purple
            'AGND': '#333333',      # Gray
            'DGND': '#4d4d4d',      # Light gray
            'VBAT': '#ffcc00'       # Yellow
        }
        
        # Check if this is a common net first
        if net_name in common_nets:
            return common_nets[net_name]
        
        # Otherwise, generate a deterministic color based on hash of net name
        import hashlib
        hash_obj = hashlib.md5(net_name.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Use the hash to generate RGB values (avoiding too dark or too light colors)
        r = ((hash_int & 0xFF0000) >> 16) % 200 + 55  # Range 55-255
        g = ((hash_int & 0x00FF00) >> 8) % 200 + 55   # Range 55-255
        b = (hash_int & 0x0000FF) % 200 + 55          # Range 55-255
        
        # Return as hex color string
        return f'#{r:02x}{g:02x}{b:02x}'

    def visualize_net_3d(self, net_name: str, output_file_path: Optional[str] = None, auto_show: bool = False):
        """
        Visualize a specified net in 3D using Plotly with advanced rendering.

        Args:
            net_name: The name of the net to visualize.
            output_file_path: Optional. If provided, saves the visualization to an HTML file.
            auto_show: Optional. If True and output_file_path is None, tries to show it in a browser.
                      Defaults to False for programmatic use.
        
        Returns:
            A Plotly Figure object or None if the net is not found.
        """
        from plotly.subplots import make_subplots
        
        net_details = self.get_trace_details(net_name)
        if not net_details:
            print(f"Net {net_name} not found or no details available.")
            return None

        # Create a figure with subplots for a more advanced 3D view
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]])

        # Extract all unique layers across the entire net's elements
        all_layers = set()
        
        # Add layers from pads
        for pad in net_details.get('pads', []):
            all_layers.add(pad['layer'])
            
        # Add layers from segments (tracks and arcs)
        for segment in net_details.get('segments', []):
            all_layers.add(segment['layer'])
            
        # Add layers from vias (both from and to layers)
        for via in net_details.get('vias', []):
            all_layers.add(via['from_layer'])
            all_layers.add(via['to_layer'])
        
        # Sort layers to ensure consistent z ordering
        all_layers = sorted(list(all_layers))
        
        # Calculate z-coordinate for each layer (space them out evenly)
        # More sophisticated z-scaling compared to original method
        layer_spacing = 15  # Increased from 10 for better visual separation
        layer_to_z = {layer: layer_spacing * i for i, layer in enumerate(all_layers)}
        
        # Get color for this net
        net_color = self._get_color_for_net(net_name)
        
        # 1. Plot Pads as markers with text labels
        x_pad, y_pad, z_pad = [], [], []
        pad_texts = []
        
        for pad in net_details.get('pads', []):
            x_pad.append(pad['x'])
            y_pad.append(pad['y'])
            # Use the layer mapping for z-coordinates
            z_pad.append(layer_to_z[pad['layer']])
            pad_texts.append(f"{pad['component']}.{pad['pad']}")
        
        if x_pad:
            # Add the pads as markers
            fig.add_trace(go.Scatter3d(
                x=x_pad, y=y_pad, z=z_pad,
                mode='markers+text',
                marker=dict(
                    size=7,  # Slightly larger for better visibility
                    color='red',
                    symbol='circle',
                    line=dict(color='black', width=1)  # Add outline for better visibility
                ),
                text=pad_texts,
                textposition='top center',
                hoverinfo='text',
                hovertext=[f"Pad: {txt}<br>Layer: {pad['layer']}<br>Net: {net_name}" 
                           for txt, pad in zip(pad_texts, net_details.get('pads', []))],
                name='Pads'
            ))

        # 2. Plot Tracks with proper color by net and improved grouping
        # Group tracks by layer for better visualization
        layer_to_tracks = {}
        for segment in net_details.get('segments', []):
            if segment['type'] == 'track':
                layer = segment['layer']
                if layer not in layer_to_tracks:
                    layer_to_tracks[layer] = []
                layer_to_tracks[layer].append(segment)
        
        # Add tracks by layer
        for layer, tracks in layer_to_tracks.items():
            x_track, y_track, z_track = [], [], []
            hover_texts = []
            
            for track in tracks:
                # Add start point
                x_track.append(track['start']['x'])
                y_track.append(track['start']['y'])
                z_track.append(layer_to_z[layer])
                hover_texts.append(f"Track<br>Layer: {layer}<br>Length: {track['length']:.2f} mils")
                
                # Add end point
                x_track.append(track['end']['x'])
                y_track.append(track['end']['y'])
                z_track.append(layer_to_z[layer])
                hover_texts.append(f"Track<br>Layer: {layer}<br>Length: {track['length']:.2f} mils")
                
                # Add None to create a break (for discontinuous lines)
                x_track.append(None)
                y_track.append(None)
                z_track.append(None)
                hover_texts.append(None)
            
            # Add the tracks for this layer
            fig.add_trace(go.Scatter3d(
                x=x_track, y=y_track, z=z_track,
                mode='lines',
                line=dict(color=net_color, width=4),
                hoverinfo='text',
                hovertext=hover_texts,
                name=f'Tracks (Layer {layer})'
            ))
        
        # 3. Plot Arcs as curved segments (better than straight lines)
        # Group arcs by layer like tracks
        layer_to_arcs = {}
        for segment in net_details.get('segments', []):
            if segment['type'] == 'arc':
                layer = segment['layer']
                if layer not in layer_to_arcs:
                    layer_to_arcs[layer] = []
                layer_to_arcs[layer].append(segment)
        
        # Add arcs by layer with improved rendering
        for layer, arcs in layer_to_arcs.items():
            for i, arc in enumerate(arcs):
                # Generate points along the arc (more accurate than straight line)
                center_x, center_y = arc['center']['x'], arc['center']['y']
                radius = arc['radius']
                start_angle = arc['start_angle']
                end_angle = arc['end_angle']
                
                # Calculate delta angle, handling wrap-around
                delta_angle = end_angle - start_angle
                if delta_angle < 0:
                    delta_angle += 360
                
                # Generate points along the arc (more points for smoother curve)
                num_segments = max(int(delta_angle / 5), 12)  # More segments for larger arcs
                x_arc, y_arc, z_arc = [], [], []
                hover_texts = []
                
                for j in range(num_segments + 1):
                    angle = start_angle + delta_angle * j / num_segments
                    angle_rad = math.radians(angle)
                    x = center_x + radius * math.cos(angle_rad)
                    y = center_y + radius * math.sin(angle_rad)
                    
                    x_arc.append(x)
                    y_arc.append(y)
                    z_arc.append(layer_to_z[layer])
                    hover_texts.append(f"Arc<br>Layer: {layer}<br>Radius: {radius:.2f} mils<br>Length: {arc['length']:.2f} mils")
                
                # Override first and last points with exact start/end from data
                if len(x_arc) > 1:
                    x_arc[0], y_arc[0] = arc['start']['x'], arc['start']['y']
                    x_arc[-1], y_arc[-1] = arc['end']['x'], arc['end']['y']
                
                # Add the arc to the figure
                fig.add_trace(go.Scatter3d(
                    x=x_arc, y=y_arc, z=z_arc,
                    mode='lines',
                    line=dict(
                        color=net_color,
                        width=3,
                        dash='solid'  # Solid line instead of dashed for arcs
                    ),
                    hoverinfo='text',
                    hovertext=hover_texts,
                    name=f'Arc-{i} (Layer {layer})'
                ))
        
        # 4. Plot Vias with improved 3D representation
        for i, via in enumerate(net_details.get('vias', [])):
            via_x, via_y = via['x'], via['y']
            from_layer_z = layer_to_z[via['from_layer']]
            to_layer_z = layer_to_z[via['to_layer']]
            
            # Create a cylinder-like structure for vias (vertical line + markers at each layer)
            # Add the vertical line connecting layers
            fig.add_trace(go.Scatter3d(
                x=[via_x, via_x],
                y=[via_y, via_y],
                z=[from_layer_z, to_layer_z],
                mode='lines',
                line=dict(color='green', width=6),
                hoverinfo='text',
                hovertext=[
                    f"Via<br>Net: {net_name}<br>From Layer: {via['from_layer']}<br>To Layer: {via['to_layer']}<br>Hole: {via['hole_size']:.1f} mils",
                    f"Via<br>Net: {net_name}<br>From Layer: {via['from_layer']}<br>To Layer: {via['to_layer']}<br>Hole: {via['hole_size']:.1f} mils"
                ],
                name=f'Via-{i}'
            ))
            
            # Add markers at each end for better visibility
            fig.add_trace(go.Scatter3d(
                x=[via_x, via_x],
                y=[via_y, via_y],
                z=[from_layer_z, to_layer_z],
                mode='markers',
                marker=dict(
                    size=5,
                    color='lightgreen',
                    symbol='circle',
                    line=dict(color='darkgreen', width=1)
                ),
                hoverinfo='text',
                hovertext=[
                    f"Via connection at Layer {via['from_layer']}",
                    f"Via connection at Layer {via['to_layer']}"
                ],
                showlegend=False
            ))
            
            # Add markers at intermediate layers that this via passes through
            if abs(via['to_layer'] - via['from_layer']) > 1:
                # Find intermediate layers
                lower_layer = min(via['from_layer'], via['to_layer'])
                upper_layer = max(via['from_layer'], via['to_layer'])
                intermediate_layers = [l for l in all_layers if lower_layer < l < upper_layer]
                
                for layer in intermediate_layers:
                    layer_z = layer_to_z[layer]
                    # Add a marker at this intermediate layer
                    fig.add_trace(go.Scatter3d(
                        x=[via_x],
                        y=[via_y],
                        z=[layer_z],
                        mode='markers',
                        marker=dict(
                            size=4,
                            color='lime',
                            symbol='circle',
                            line=dict(color='darkgreen', width=1)
                        ),
                        hoverinfo='text',
                        hovertext=[f"Via passing through Layer {layer}"],
                        showlegend=False
                    ))

        # Create the layout with improved settings
        layout = dict(
            title=dict(
                text=f'3D Visualization of Net: {net_name}',
                font=dict(size=16, color='black')
            ),
            scene=dict(
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.0),  # Better initial camera position
                ),
                xaxis=dict(
                    title='X (mils)',
                    gridcolor='lightgray',
                    showbackground=True,
                    backgroundcolor='rgb(245, 245, 245)'
                ),
                yaxis=dict(
                    title='Y (mils)',
                    gridcolor='lightgray',
                    showbackground=True,
                    backgroundcolor='rgb(245, 245, 245)'
                ),
                zaxis=dict(
                    title='Layer',
                    gridcolor='lightgray',
                    showbackground=True,
                    backgroundcolor='rgb(245, 245, 245)'
                ),
                aspectmode='data'  # Keep data aspect ratio
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            legend=dict(
                x=0,
                y=1,
                bgcolor='rgba(255, 255, 255, 0.7)',
                bordercolor='gray',
                borderwidth=1
            ),
            hovermode='closest'
        )

        # Update the figure layout
        fig.update_layout(layout)

        # Save or show the figure
        if output_file_path:
            fig.write_html(output_file_path)
            print(f"3D visualization saved to {output_file_path}")
        elif auto_show:
            fig.show()  # Opens in browser

        return fig

    def get_components_by_net(self, net_name: str) -> List[dict]:
        """
        Get all components connected to a specific net.
        
        Args:
            net_name: The name of the net to find components for
            
        Returns:
            List of component objects with their pads connected to the net
        """
        components = {}
        
        # Get all pads on this net
        for obj in self.objects:
            if isinstance(obj, Pad) and obj.net_name == net_name:
                # Add component to the dict if not already present
                if obj.designator not in components:
                    components[obj.designator] = {
                        "designator": obj.designator,
                        "pads": []
                    }
                
                # Add this pad to the component
                components[obj.designator]["pads"].append({
                    "padNumber": obj.pad_number,
                    "netName": obj.net_name
                })
        
        # Return as a list for the API
        return list(components.values())

if __name__ == "__main__":
    # Example Usage for visualize_net_3d

    # 1. Define a simple sample PCB data structure
    sample_pcb_data = {
        "components": [
            {
                "designator": "U1", "layer": 1,
                "pads": [
                    {"padNumber": "1", "netName": "NetA", "location": {"x": 100, "y": 100}, "layer": 1, "width": 10, "height": 10},
                    {"padNumber": "2", "netName": "NetA", "location": {"x": 500, "y": 500}, "layer": 2, "width": 10, "height": 10}
                ]
            },
            {
                "designator": "R1", "layer": 1,
                "pads": [
                    {"padNumber": "1", "netName": "NetA", "location": {"x": 100, "y": 300}, "layer": 1, "width": 8, "height": 8},
                ]
            }
        ],
        "tracks": [
            {"start": {"x": 100, "y": 100}, "end": {"x": 100, "y": 250}, "netName": "NetA", "layer": 1, "length": 150},
            {"start": {"x": 100, "y": 250}, "end": {"x": 100, "y": 300}, "netName": "NetA", "layer": 1, "length": 50},
            # A track on layer 2 connecting to where a via might end up
            {"start": {"x": 300, "y": 300}, "end": {"x": 500, "y": 500}, "netName": "NetA", "layer": 2, "length": 282.8}
        ],
        "vias": [
            {"location": {"x": 100, "y": 250}, "netName": "NetA", "fromLayer": 1, "toLayer": 2, "holeSize": 20},
             # Add another via to connect the track on layer 2 to U1.2
            {"location": {"x": 300, "y": 300}, "netName": "NetA", "fromLayer": 1, "toLayer": 2, "holeSize": 20}
        ],
        "arcs": []
    }

    # 2. Create an instance of PCBTraceExtractor
    print("Creating PCBTraceExtractor with sample data...")
    extractor = PCBTraceExtractor(pcb_data=sample_pcb_data)

    # 3. Choose a net to visualize
    net_to_visualize = "NetA"
    output_html_file = f"{net_to_visualize}_3d_visualization.html"

    print(f"Visualizing net: {net_to_visualize} in 3D...")
    # 4. Call the visualize_net_3d method
    # Pass auto_show=True if you want the __main__ block to open the browser when no file path is given.
    # For just saving to file, auto_show=False (default) is fine.
    fig = extractor.visualize_net_3d(net_name=net_to_visualize, output_file_path=output_html_file, auto_show=False)

    if fig:
        print(f"Successfully generated 3D visualization for {net_to_visualize}.")
        print(f"Output saved to: {output_html_file}")
    else:
        print(f"Failed to generate 3D visualization for {net_to_visualize}.")

    # You can also try the 2D visualization for comparison
    # output_png_file = f"{net_to_visualize}_2d_visualization.png"
    # print(f"Visualizing net: {net_to_visualize} in 2D...")
    # fig_2d = extractor.visualize_net(net_name=net_to_visualize, output_path=output_png_file)
    # if fig_2d:
    #     print(f"Successfully generated 2D visualization for {net_to_visualize}.")
    #     print(f"Output saved to: {output_png_file}")
    # else:
    #     print(f"Failed to generate 2D visualization for {net_to_visualize}.")