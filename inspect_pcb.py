#!/usr/bin/env python3
import json
from collections import defaultdict

# Load the PCB data
with open('Vacuum_PCB_Objects.json', 'r') as f:
    data = json.load(f)

# Group tracks by net name and calculate total track length per net
tracks_by_net = defaultdict(list)
total_length_by_net = defaultdict(float)

for track in data.get('tracks', []):
    net_name = track.get('netName')
    if net_name:
        tracks_by_net[net_name].append(track)
        total_length_by_net[net_name] += track.get('length', 0)

# Find nets with the most total track length (these are likely to have longer paths)
nets_by_total_length = sorted(total_length_by_net.items(), key=lambda x: x[1], reverse=True)
top_nets = [net for net, length in nets_by_total_length[:10]]
print("Top 10 nets by total track length:")
for i, (net, length) in enumerate(nets_by_total_length[:10]):
    print(f"{i+1}. {net}: {length:.1f} mils total length")

# Group pads by net name with their position
pads_by_net = defaultdict(list)
for comp in data.get('components', []):
    designator = comp['designator']
    for pad in comp.get('pads', []):
        net_name = pad.get('netName')
        if net_name:
            pad_info = {
                'component': designator,
                'pad': pad['padNumber'],
                'x': pad['location']['x'],
                'y': pad['location']['y']
            }
            pads_by_net[net_name].append(pad_info)

# Look for paths with multiple segments
connection_tolerance = 50.0  # increased tolerance in mils
min_track_length = 75.0     # minimum track length for individual tracks

# Function to check if components are different
def different_components(pad1, pad2):
    return pad1['component'] != pad2['component']

# Find paths to test using the top nets
print("\nChecking top nets for trace calculations:")

potential_paths = []

for net_name in top_nets:
    print(f"\n* Net: {net_name}")
    print(f"  - Contains {len(pads_by_net[net_name])} pads and {len(tracks_by_net[net_name])} tracks")
    
    # Get all tracks for this net
    all_tracks = tracks_by_net[net_name]
    # Find tracks with significant length
    longer_tracks = [t for t in all_tracks if t.get('length', 0) > min_track_length]
    print(f"  - Found {len(longer_tracks)} tracks longer than {min_track_length} mils")
    
    if not longer_tracks:
        continue
    
    # Build dictionary of pad pairs to check later
    pad_pairs_to_check = []
    # Focus on pads that are far apart spatially
    all_pads = pads_by_net[net_name]
    for i, pad1 in enumerate(all_pads):
        for pad2 in all_pads[i+1:]:
            if different_components(pad1, pad2):
                # Calculate Euclidean distance between pads
                dist = ((pad1['x'] - pad2['x'])**2 + (pad1['y'] - pad2['y'])**2)**0.5
                pad_pairs_to_check.append((pad1, pad2, dist))
    
    # Sort by distance and take the top 20 (likely to have longer traces)
    pad_pairs_to_check.sort(key=lambda x: x[2], reverse=True)
    for pad1, pad2, dist in pad_pairs_to_check[:20]:
        # Add to potential paths to check
        potential_paths.append({
            'net_name': net_name,
            'pad1': pad1,
            'pad2': pad2,
            'spatial_distance': dist,
            'potential_length': dist  # Use spatial distance as an approximation
        })

# Sort by potential length (spatial distance)
potential_paths.sort(key=lambda x: x['spatial_distance'], reverse=True)

# Print potential paths found
print("\n\nPotential longer connections to test:")
if potential_paths:
    for i, path in enumerate(potential_paths[:15]):  # Show top 15
        pad1 = path['pad1']
        pad2 = path['pad2']
        print(f"\n{i+1}. {path['net_name']}: {pad1['component']}.{pad1['pad']} -> {pad2['component']}.{pad2['pad']} (Est. distance: {path['spatial_distance']:.1f} mils)")
        print(f"   curl -X POST -H \"Content-Type: application/json\" -d '{{\"net_name\":\"{path['net_name']}\", \"start_component\":\"{pad1['component']}\", \"start_pad\":\"{pad1['pad']}\", \"end_component\":\"{pad2['component']}\", \"end_pad\":\"{pad2['pad']}\"}}' http://localhost:8000/board/ee5bf4a3-1300-4d7f-be58-ec77395171da/calculate_trace")
else:
    print("No potential paths found with the current criteria.") 