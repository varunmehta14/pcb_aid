import json
import os
from trace_extractor import PCBTraceExtractor, PCBLayer, PCBStackup

def test_calculate_trace_impedance():
    """Test the calculate_trace_impedance method on a PCB trace."""
    # Create a PCB extractor instance
    extractor = PCBTraceExtractor()
    
    # Check if test data exists, if not, create minimal test data
    test_file = "test_pcb_data.json"
    if not os.path.exists(test_file):
        create_test_data(test_file)
    
    # Load the test data
    extractor.load_json_file(test_file)
    
    # Test the impedance calculation between two specific pads
    result = extractor.calculate_trace_impedance("R1", "1", "C1", "1")
    
    # Print the results
    if result:
        print("\nImpedance Calculation Results:")
        print(f"Average Impedance: {result['impedance_ohms']:.2f} ohms")
        print(f"Trace Width: {result['trace_width']:.2f} mils")
        print(f"Dielectric Constant: {result['dielectric_constant']}")
        print(f"Minimum Impedance: {result.get('min_impedance', 'N/A'):.2f} ohms")
        print(f"Maximum Impedance: {result['max_impedance']:.2f} ohms")
        print(f"Total Length: {result['total_length_mm']:.2f} mm ({result['total_length_mils']:.2f} mils)")
        
        print("\nSegment Details:")
        for i, segment in enumerate(result['segments']):
            print(f"Segment {i+1}: {segment['type']} on layer {segment['layer']}")
            print(f"  Width: {segment['width']:.2f} mils")
            print(f"  Length: {segment['length']:.2f} mils")
            print(f"  Impedance: {segment['impedance']:.2f} ohms")
    else:
        print("Could not calculate impedance. Check if a valid path exists between the specified pads.")

def create_test_data(filename):
    """Create minimal test PCB data for impedance calculation."""
    test_data = {
        "components": [
            {
                "designator": "R1",
                "layer": 1,
                "pads": [
                    {
                        "padNumber": "1",
                        "netName": "NET1",
                        "location": {"x": 1000, "y": 1000},
                        "width": 20,
                        "height": 20,
                        "shape": "Round"
                    },
                    {
                        "padNumber": "2",
                        "netName": "NET2",
                        "location": {"x": 1200, "y": 1000},
                        "width": 20,
                        "height": 20,
                        "shape": "Round"
                    }
                ]
            },
            {
                "designator": "C1",
                "layer": 1,
                "pads": [
                    {
                        "padNumber": "1",
                        "netName": "NET1",
                        "location": {"x": 1500, "y": 1000},
                        "width": 20,
                        "height": 20,
                        "shape": "Round"
                    },
                    {
                        "padNumber": "2",
                        "netName": "GND",
                        "location": {"x": 1500, "y": 1200},
                        "width": 20,
                        "height": 20,
                        "shape": "Round"
                    }
                ]
            }
        ],
        "tracks": [
            {
                "start": {"x": 1000, "y": 1000},
                "end": {"x": 1250, "y": 1000},
                "netName": "NET1",
                "layer": 1,
                "length": 250,
                "width": 10
            },
            {
                "start": {"x": 1250, "y": 1000},
                "end": {"x": 1500, "y": 1000},
                "netName": "NET1",
                "layer": 1,
                "length": 250,
                "width": 10
            }
        ],
        "arcs": [],
        "vias": []
    }
    
    # Add width to tracks
    for track in test_data["tracks"]:
        track["width"] = 10.0  # 10 mil trace width
    
    # Save the test data
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Created test data file: {filename}")

if __name__ == "__main__":
    test_calculate_trace_impedance() 