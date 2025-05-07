# trace_extractor.py
import json
import math
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.ops import nearest_points
from shapely.affinity import rotate, translate
# import numpy as np # Not used
from collections import defaultdict, deque
# import matplotlib.pyplot as plt # Keep commented out unless visualizing

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
    Robust PCB trace extractor that uses a sophisticated path finding algorithm
    with multiple fallback mechanisms to ensure accurate trace length calculation.
    """
    def __init__(self):
        self.objects = []
        self.pads = []
        self.pad_cache = {}  # Cache for pad lookups by designation and pad number
        self.connection_cache = {}  # Cache for connection results

    def load_json_file(self, path: str):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {path}")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {path}")
            return

        # Clear previous data
        self.objects = []
        self.pads = []
        self.pad_cache = {}
        self.connection_cache = {} # Clear cache on new load

        # parse pads
        for c in data.get('components', []):
            d = c['designator']
            # Use component layer if pad doesn't specify, default to 1 if neither specifies
            comp_layer = c.get('layer', 1)
            for p in c.get('pads', []):
                pad_layer = p.get('layer', comp_layer) # Pad layer overrides component layer
                pad = Pad(
                    designator=d,
                    pad_number=str(p['padNumber']),
                    net_name=p['netName'],
                    location=(p['location']['x'], p['location']['y']), # Assume mils
                    layer=pad_layer,
                    width=p.get('width', 0),
                    height=p.get('height', 0),
                    hole_size=p.get('holeSize', 0),
                    rotation=p.get('rotation', 0),
                    shape=p.get('shape', 'Rectangular') # Default shape
                )
                # Only add pads with net names
                if pad.net_name:
                    self.objects.append(pad)
                    self.pads.append(pad)
                    self.pad_cache[(d, str(p['padNumber']))] = pad
        # parse tracks
        for t in data.get('tracks', []):
            track = Track(
                start=(t['start']['x'], t['start']['y']), # Assume mils
                end=(t['end']['x'], t['end']['y']),       # Assume mils
                net_name=t['netName'],
                layer=t['layer'],
                length=t['length'] # Assume mils
            )
            # Only add tracks with net names and non-zero length (or handle zero-length if needed)
            if track.net_name and track.length > 1e-6:
                 self.objects.append(track)

        # parse arcs
        for a in data.get('arcs', []):
            arc = Arc(
                center=(a['center']['x'], a['center']['y']), # Assume mils
                radius=a['radius'],                           # Assume mils
                start_angle=a['startAngle'],                  # Assume degrees
                end_angle=a['endAngle'],                      # Assume degrees
                start=(a['start']['x'], a['start']['y']),     # Assume mils
                end=(a['end']['x'], a['end']['y']),           # Assume mils
                net_name=a['netName'],
                layer=a['layer'],
                length=a['length'] # Assume mils
            )
            # Only add arcs with net names and non-zero length
            if arc.net_name and arc.length > 1e-6:
                self.objects.append(arc)

        # parse vias
        for v in data.get('vias', []):
            via = Via(
                location=(v['location']['x'], v['location']['y']), # Assume mils
                net_name=v['netName'],
                from_layer=v['fromLayer'],
                to_layer=v['toLayer'],
                hole_size=v.get('holeSize', 0) # Assume mils
            )
            # Only add vias with net names
            if via.net_name:
                self.objects.append(via)

        print(f"Loaded {len(self.objects)} objects ({len(self.pads)} pads).") # Debug print

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


        # Cache the result (even if None)
        self.connection_cache[cache_key] = shortest_length

        if shortest_length is not None:
            if debug: print(f"Final Result: Length={shortest_length:.5f} mm using {strategy_used}")
            return shortest_length
        else:
            if debug: print(f"No path found between {c1}.{p1} and {c2}.{p2} using any strategy.")
            return None

    def extract_traces(self, component1, pad1, component2, pad2):
        """Compatibility method"""
        return self.extract_traces_between_pads(component1, pad1, component2, pad2)