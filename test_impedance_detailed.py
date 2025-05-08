import json
import os
import math
from trace_extractor import PCBTraceExtractor, PCBLayer, PCBStackup

def test_impedance_calculation_with_different_widths():
    """Test impedance calculation with different trace widths."""
    # Create test file with traces of different widths on the same net
    test_file = "test_impedance_widths.json"
    create_test_data_with_different_widths(test_file)
    
    # Create extractor and load the test data
    extractor = PCBTraceExtractor()
    extractor.load_json_file(test_file)
    
    # Calculate impedance
    result = extractor.calculate_trace_impedance("R1", "1", "C1", "1")
    
    # Print results
    print("\n=== Impedance Test with Different Trace Widths ===")
    if result:
        print(f"Average Impedance: {result['impedance_ohms']:.2f} ohms")
        print(f"Average Width: {result['trace_width']:.2f} mils")
        
        print("\nSegment Details:")
        for i, segment in enumerate(result['segments']):
            print(f"Segment {i+1}: Width={segment['width']:.2f} mils, Impedance={segment['impedance']:.2f} ohms")
    else:
        print("Could not calculate impedance.")

def test_impedance_calculation_with_different_layers():
    """Test impedance calculation with traces on different layers."""
    # Create test file with traces on different layers
    test_file = "test_impedance_layers.json"
    create_test_data_with_different_layers(test_file)
    
    # Create extractor and load the test data
    extractor = PCBTraceExtractor()
    extractor.load_json_file(test_file)
    
    # Calculate impedance
    result = extractor.calculate_trace_impedance("R1", "1", "C1", "1")
    
    # Print results
    print("\n=== Impedance Test with Different Layers ===")
    if result:
        print(f"Average Impedance: {result['impedance_ohms']:.2f} ohms")
        
        print("\nSegment Details:")
        for i, segment in enumerate(result['segments']):
            print(f"Segment {i+1}: Layer={segment['layer']}, Type={segment['type']}, Impedance={segment['impedance']:.2f} ohms")
    else:
        print("Could not calculate impedance.")

def test_impedance_calculation_with_complex_path():
    """Test impedance calculation with a complex path including vias."""
    # Create test file with a complex path
    test_file = "test_impedance_complex.json"
    create_test_data_with_complex_path(test_file)
    
    # Create extractor and load the test data
    extractor = PCBTraceExtractor()
    extractor.load_json_file(test_file)
    
    # Calculate impedance
    result = extractor.calculate_trace_impedance("R1", "1", "C1", "1")
    
    # Print results
    print("\n=== Impedance Test with Complex Path ===")
    if result:
        print(f"Average Impedance: {result['impedance_ohms']:.2f} ohms")
        print(f"Minimum Impedance: {result.get('min_impedance', 'N/A'):.2f} ohms")
        print(f"Maximum Impedance: {result['max_impedance']:.2f} ohms")
        print(f"Total Length: {result['total_length_mm']:.2f} mm ({result['total_length_mils']:.2f} mils)")
        
        print("\nSegment Details:")
        for i, segment in enumerate(result['segments']):
            print(f"Segment {i+1}: Layer={segment['layer']}, Type={segment['type']}, Impedance={segment['impedance']:.2f} ohms")
    else:
        print("Could not calculate impedance for complex path.")

def create_test_data_with_different_widths(filename):
    """Create test data with traces of different widths."""
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
                        "location": {"x": 1600, "y": 1000},
                        "width": 20,
                        "height": 20,
                        "shape": "Round"
                    },
                    {
                        "padNumber": "2",
                        "netName": "GND",
                        "location": {"x": 1600, "y": 1200},
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
                "end": {"x": 1300, "y": 1000},
                "netName": "NET1",
                "layer": 1,
                "length": 300,
                "width": 5  # Narrow trace
            },
            {
                "start": {"x": 1300, "y": 1000},
                "end": {"x": 1600, "y": 1000},
                "netName": "NET1",
                "layer": 1,
                "length": 300,
                "width": 15  # Wide trace
            }
        ],
        "arcs": [],
        "vias": []
    }
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Created test data file with different widths: {filename}")

def create_test_data_with_different_layers(filename):
    """Create test data with traces on different layers."""
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
                        "shape": "Round",
                        "holeSize": 10  # Through-hole pad
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
                "layer": 7,  # Bottom layer
                "pads": [
                    {
                        "padNumber": "1",
                        "netName": "NET1",
                        "location": {"x": 1600, "y": 1000},
                        "width": 20,
                        "height": 20,
                        "shape": "Round",
                        "holeSize": 10  # Through-hole pad
                    },
                    {
                        "padNumber": "2",
                        "netName": "GND",
                        "location": {"x": 1600, "y": 1200},
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
                "end": {"x": 1200, "y": 1000},
                "netName": "NET1",
                "layer": 1,  # Top layer
                "length": 200,
                "width": 10
            },
            {
                "start": {"x": 1200, "y": 1000},
                "end": {"x": 1400, "y": 1000},
                "netName": "NET1",
                "layer": 3,  # Inner layer (GND plane)
                "length": 200,
                "width": 10
            },
            {
                "start": {"x": 1400, "y": 1000},
                "end": {"x": 1600, "y": 1000},
                "netName": "NET1",
                "layer": 7,  # Bottom layer
                "length": 200,
                "width": 10
            }
        ],
        "vias": [
            {
                "location": {"x": 1200, "y": 1000},
                "netName": "NET1",
                "fromLayer": 1,
                "toLayer": 3,
                "holeSize": 8
            },
            {
                "location": {"x": 1400, "y": 1000},
                "netName": "NET1",
                "fromLayer": 3,
                "toLayer": 7,
                "holeSize": 8
            }
        ],
        "arcs": []
    }
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Created test data file with different layers: {filename}")

def create_test_data_with_complex_path(filename):
    """Create test data with a complex path including vias and multiple segments."""
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
                        "shape": "Round",
                        "holeSize": 10
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
                        "location": {"x": 1800, "y": 1400},
                        "width": 20,
                        "height": 20,
                        "shape": "Round",
                        "holeSize": 10
                    },
                    {
                        "padNumber": "2",
                        "netName": "GND",
                        "location": {"x": 1800, "y": 1600},
                        "width": 20,
                        "height": 20,
                        "shape": "Round"
                    }
                ]
            }
        ],
        "tracks": [
            # First segment - top layer horizontal
            {
                "start": {"x": 1000, "y": 1000},
                "end": {"x": 1200, "y": 1000},
                "netName": "NET1",
                "layer": 1,
                "length": 200,
                "width": 8
            },
            # Second segment - top layer vertical
            {
                "start": {"x": 1200, "y": 1000},
                "end": {"x": 1200, "y": 1200},
                "netName": "NET1",
                "layer": 1,
                "length": 200,
                "width": 8
            },
            # Third segment - inner layer horizontal
            {
                "start": {"x": 1200, "y": 1200},
                "end": {"x": 1600, "y": 1200},
                "netName": "NET1",
                "layer": 3,
                "length": 400,
                "width": 12
            },
            # Fourth segment - bottom layer vertical
            {
                "start": {"x": 1600, "y": 1200},
                "end": {"x": 1600, "y": 1400},
                "netName": "NET1",
                "layer": 7,
                "length": 200,
                "width": 10
            },
            # Fifth segment - bottom layer horizontal
            {
                "start": {"x": 1600, "y": 1400},
                "end": {"x": 1800, "y": 1400},
                "netName": "NET1",
                "layer": 7,
                "length": 200,
                "width": 10
            }
        ],
        "vias": [
            {
                "location": {"x": 1200, "y": 1200},
                "netName": "NET1",
                "fromLayer": 1,
                "toLayer": 3,
                "holeSize": 8
            },
            {
                "location": {"x": 1600, "y": 1200},
                "netName": "NET1",
                "fromLayer": 3,
                "toLayer": 7,
                "holeSize": 8
            }
        ],
        "arcs": []
    }
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Created test data file with complex path: {filename}")

if __name__ == "__main__":
    # Run all tests
    test_impedance_calculation_with_different_widths()
    test_impedance_calculation_with_different_layers()
    test_impedance_calculation_with_complex_path() 