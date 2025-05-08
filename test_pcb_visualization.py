import os
import json
import unittest
from trace_extractor import PCBTraceExtractor

class TestPCBVisualization(unittest.TestCase):
    """Test suite for PCB visualization functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PCBTraceExtractor()
        
        # Create test data files
        self.simple_test_file = "test_viz_simple.json"
        self.multilayer_test_file = "test_viz_multilayer.json"
        self.complex_test_file = "test_viz_complex.json"
        
        # Create different test data variations
        self.create_simple_pcb_data(self.simple_test_file)
        self.create_multilayer_pcb_data(self.multilayer_test_file)
        self.create_complex_pcb_data(self.complex_test_file)
        
        # Output files
        self.output_files = []
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test data files
        for file_path in [self.simple_test_file, self.multilayer_test_file, self.complex_test_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove generated visualization files
        for output_file in self.output_files:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def create_simple_pcb_data(self, filename):
        """Create simple PCB test data with a few components on a single layer."""
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
                            "location": {"x": 1000, "y": 1300},
                            "width": 20,
                            "height": 20,
                            "shape": "Round"
                        },
                        {
                            "padNumber": "2",
                            "netName": "GND",
                            "location": {"x": 1200, "y": 1300},
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
                    "end": {"x": 1000, "y": 1300},
                    "netName": "NET1",
                    "layer": 1,
                    "length": 300,
                    "width": 10
                },
                {
                    "start": {"x": 1200, "y": 1000},
                    "end": {"x": 1200, "y": 1300},
                    "netName": "NET2",
                    "layer": 1,
                    "length": 300,
                    "width": 10
                }
            ],
            "arcs": [],
            "vias": []
        }
        
        with open(filename, 'w') as f:
            json.dump(test_data, f, indent=2)
    
    def create_multilayer_pcb_data(self, filename):
        """Create more complex PCB test data with multiple layers."""
        test_data = {
            "components": [
                {
                    "designator": "U1",
                    "layer": 1,
                    "pads": [
                        {
                            "padNumber": "1",
                            "netName": "NET1",
                            "location": {"x": 1000, "y": 1000},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "2",
                            "netName": "NET2",
                            "location": {"x": 1050, "y": 1000},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "3",
                            "netName": "NET3",
                            "location": {"x": 1100, "y": 1000},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "4",
                            "netName": "GND",
                            "location": {"x": 1100, "y": 1050},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "5",
                            "netName": "NET5",
                            "location": {"x": 1100, "y": 1100},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "6",
                            "netName": "NET6",
                            "location": {"x": 1050, "y": 1100},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "7",
                            "netName": "NET7",
                            "location": {"x": 1000, "y": 1100},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        },
                        {
                            "padNumber": "8",
                            "netName": "VCC",
                            "location": {"x": 1000, "y": 1050},
                            "width": 20,
                            "height": 20,
                            "shape": "Rectangle"
                        }
                    ]
                },
                {
                    "designator": "C2",
                    "layer": 1,
                    "pads": [
                        {
                            "padNumber": "1",
                            "netName": "VCC",
                            "location": {"x": 1300, "y": 1000},
                            "width": 25,
                            "height": 25,
                            "shape": "Round",
                            "holeSize": 10
                        },
                        {
                            "padNumber": "2",
                            "netName": "GND",
                            "location": {"x": 1300, "y": 1100},
                            "width": 25,
                            "height": 25,
                            "shape": "Round",
                            "holeSize": 10
                        }
                    ]
                },
                {
                    "designator": "R3",
                    "layer": 7, # Bottom layer
                    "pads": [
                        {
                            "padNumber": "1",
                            "netName": "NET5",
                            "location": {"x": 1200, "y": 1200},
                            "width": 20,
                            "height": 20,
                            "shape": "Round",
                            "holeSize": 10
                        },
                        {
                            "padNumber": "2",
                            "netName": "GND",
                            "location": {"x": 1300, "y": 1200},
                            "width": 20,
                            "height": 20,
                            "shape": "Round",
                            "holeSize": 10
                        }
                    ]
                }
            ],
            "tracks": [
                # Top layer tracks
                {
                    "start": {"x": 1000, "y": 1050},
                    "end": {"x": 1300, "y": 1000},
                    "netName": "VCC",
                    "layer": 1,
                    "length": 301.66,
                    "width": 15
                },
                {
                    "start": {"x": 1100, "y": 1050},
                    "end": {"x": 1300, "y": 1100},
                    "netName": "GND",
                    "layer": 1,
                    "length": 201.66,
                    "width": 15
                },
                # Inner layer tracks
                {
                    "start": {"x": 1100, "y": 1100},
                    "end": {"x": 1150, "y": 1200},
                    "netName": "NET5",
                    "layer": 3,
                    "length": 111.80,
                    "width": 10
                },
                # Bottom layer tracks
                {
                    "start": {"x": 1150, "y": 1200},
                    "end": {"x": 1200, "y": 1200},
                    "netName": "NET5",
                    "layer": 7,
                    "length": 50,
                    "width": 10
                }
            ],
            "arcs": [
                {
                    "center": {"x": 1150, "y": 1000},
                    "radius": 50,
                    "startAngle": 0,
                    "endAngle": 180,
                    "start": {"x": 1200, "y": 1000},
                    "end": {"x": 1100, "y": 1000},
                    "netName": "NET3",
                    "layer": 1,
                    "length": 157.08
                }
            ],
            "vias": [
                {
                    "location": {"x": 1150, "y": 1200},
                    "netName": "NET5",
                    "fromLayer": 3,
                    "toLayer": 7,
                    "holeSize": 8
                },
                {
                    "location": {"x": 1100, "y": 1100},
                    "netName": "NET5",
                    "fromLayer": 1,
                    "toLayer": 3,
                    "holeSize": 8
                }
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(test_data, f, indent=2)
    
    def create_complex_pcb_data(self, filename):
        """Create a complex PCB with many components, dense routing, and multiple nets."""
        # Create a grid of components with interconnections
        components = []
        tracks = []
        vias = []
        
        # Add a grid of resistors
        for i in range(4):
            for j in range(3):
                designator = f"R{i*3+j+1}"
                x_pos = 1000 + i * 300
                y_pos = 1000 + j * 300
                
                # Create net names
                net_a = f"NET_A{i}{j}"
                net_b = f"NET_B{i}{j}"
                
                # Add component
                components.append({
                    "designator": designator,
                    "layer": 1,
                    "pads": [
                        {
                            "padNumber": "1",
                            "netName": net_a,
                            "location": {"x": x_pos, "y": y_pos},
                            "width": 20,
                            "height": 20,
                            "shape": "Round"
                        },
                        {
                            "padNumber": "2",
                            "netName": net_b,
                            "location": {"x": x_pos + 100, "y": y_pos},
                            "width": 20,
                            "height": 20,
                            "shape": "Round"
                        }
                    ]
                })
                
                # Add horizontal tracks connecting adjacent resistors in rows
                if i < 3:
                    tracks.append({
                        "start": {"x": x_pos + 100, "y": y_pos},
                        "end": {"x": x_pos + 200, "y": y_pos},
                        "netName": net_b,
                        "layer": 1,
                        "length": 100,
                        "width": 10
                    })
                
                # Add vertical tracks connecting resistors in columns (on inner layer)
                if j < 2:
                    # Via down to inner layer
                    vias.append({
                        "location": {"x": x_pos, "y": y_pos},
                        "netName": net_a,
                        "fromLayer": 1,
                        "toLayer": 3,
                        "holeSize": 8
                    })
                    
                    # Track on inner layer
                    tracks.append({
                        "start": {"x": x_pos, "y": y_pos},
                        "end": {"x": x_pos, "y": y_pos + 300},
                        "netName": net_a,
                        "layer": 3,
                        "length": 300,
                        "width": 8
                    })
                    
                    # Via back up to top layer
                    vias.append({
                        "location": {"x": x_pos, "y": y_pos + 300},
                        "netName": net_a,
                        "fromLayer": 3,
                        "toLayer": 1,
                        "holeSize": 8
                    })
        
        # Add IC and decoupling capacitor
        ic_component = {
            "designator": "U1",
            "layer": 1,
            "pads": []
        }
        
        # Add 16 pads to the IC
        for i in range(16):
            x_offset = 0
            y_offset = 0
            
            if i < 4:  # Bottom row
                x_offset = 50 * i
                y_offset = 0
            elif i < 8:  # Right column
                x_offset = 150
                y_offset = 50 * (i - 4)
            elif i < 12:  # Top row
                x_offset = 150 - 50 * (i - 8)
                y_offset = 150
            else:  # Left column
                x_offset = 0
                y_offset = 150 - 50 * (i - 12)
            
            pad = {
                "padNumber": str(i + 1),
                "netName": f"IC_NET{i+1}",
                "location": {"x": 2000 + x_offset, "y": 1500 + y_offset},
                "width": 20,
                "height": 20,
                "shape": "Rectangle"
            }
            
            ic_component["pads"].append(pad)
        
        components.append(ic_component)
        
        # Add decoupling capacitor
        components.append({
            "designator": "C10",
            "layer": 1,
            "pads": [
                {
                    "padNumber": "1",
                    "netName": "IC_NET1",  # VCC
                    "location": {"x": 1900, "y": 1400},
                    "width": 25,
                    "height": 25,
                    "shape": "Round"
                },
                {
                    "padNumber": "2",
                    "netName": "IC_NET12",  # GND
                    "location": {"x": 1900, "y": 1600},
                    "width": 25,
                    "height": 25,
                    "shape": "Round"
                }
            ]
        })
        
        # Add tracks from IC to capacitor
        tracks.append({
            "start": {"x": 2000, "y": 1500},  # IC pin 1
            "end": {"x": 1900, "y": 1400},    # Capacitor pin 1
            "netName": "IC_NET1",
            "layer": 1,
            "length": 141.42,
            "width": 15
        })
        
        tracks.append({
            "start": {"x": 2000, "y": 1650},  # IC pin 12
            "end": {"x": 1900, "y": 1600},    # Capacitor pin 2
            "netName": "IC_NET12",
            "layer": 1,
            "length": 111.80,
            "width": 15
        })
        
        # Add a ground plane on layer 3 (inner layer)
        # This would be represented as a polygon, but we'll just create tracks for visualization
        for i in range(10):
            tracks.append({
                "start": {"x": 1800 + i*50, "y": 1800},
                "end": {"x": 1800 + i*50, "y": 2000},
                "netName": "IC_NET12",  # GND
                "layer": 3,
                "length": 200,
                "width": 10
            })
        
        # Compile the full dataset
        test_data = {
            "components": components,
            "tracks": tracks,
            "vias": vias,
            "arcs": []
        }
        
        with open(filename, 'w') as f:
            json.dump(test_data, f, indent=2)
    
    def test_generate_3d_visualization(self):
        """Test the 3D visualization generation for different board complexities."""
        # Test with simple board
        self.extractor.load_json_file(self.simple_test_file)
        output_file = "simple_3d_viz.html"
        self.output_files.append(output_file)
        
        fig = self.extractor.generate_3d_visualization(output_file=output_file)
        self.assertIsNotNone(fig, "Failed to generate 3D visualization for simple board")
        self.assertTrue(os.path.exists(output_file), f"Output file {output_file} was not created")
        
        # Test with multilayer board
        self.extractor.load_json_file(self.multilayer_test_file)
        output_file = "multilayer_3d_viz.html"
        self.output_files.append(output_file)
        
        fig = self.extractor.generate_3d_visualization(output_file=output_file)
        self.assertIsNotNone(fig, "Failed to generate 3D visualization for multilayer board")
        self.assertTrue(os.path.exists(output_file), f"Output file {output_file} was not created")
        
        # Test with complex board
        self.extractor.load_json_file(self.complex_test_file)
        output_file = "complex_3d_viz.html"
        self.output_files.append(output_file)
        
        fig = self.extractor.generate_3d_visualization(output_file=output_file)
        self.assertIsNotNone(fig, "Failed to generate 3D visualization for complex board")
        self.assertTrue(os.path.exists(output_file), f"Output file {output_file} was not created")
    
    def test_visualize_path(self):
        """Test visualization of a specific path between components."""
        # Test with multilayer board
        self.extractor.load_json_file(self.multilayer_test_file)
        output_file = "path_visualization.html"
        self.output_files.append(output_file)
        
        # Visualize path between U1 pin 5 and R3 pin 1 (NET5)
        fig = self.extractor.visualize_path("U1", "5", "R3", "1", output_file=output_file)
        self.assertIsNotNone(fig, "Failed to generate path visualization")
        self.assertTrue(os.path.exists(output_file), f"Output file {output_file} was not created")
        
        # Test with complex board
        self.extractor.load_json_file(self.complex_test_file)
        output_file = "complex_path_visualization.html"
        self.output_files.append(output_file)
        
        # Visualize path between U1 pin 1 and C10 pin 1 (IC_NET1)
        fig = self.extractor.visualize_path("U1", "1", "C10", "1", output_file=output_file)
        self.assertIsNotNone(fig, "Failed to generate path visualization for complex board")
        self.assertTrue(os.path.exists(output_file), f"Output file {output_file} was not created")
    
    def test_color_generation(self):
        """Test the color generation function for nets."""
        # Test color generation for different nets
        nets = ["VCC", "GND", "NET1", "NET2", "NET3", "SIGNAL"]
        colors = [self.extractor._get_color_for_net(net) for net in nets]
        
        # Check all colors are in RGB format
        for color in colors:
            self.assertTrue(color.startswith('rgb('), f"Color {color} not in RGB format")
            self.assertTrue(color.endswith(')'), f"Color {color} not in RGB format")
        
        # Check colors are consistent for the same net
        for net in nets:
            color1 = self.extractor._get_color_for_net(net)
            color2 = self.extractor._get_color_for_net(net)
            self.assertEqual(color1, color2, f"Colors for same net '{net}' are inconsistent")
        
        # Check different nets get different colors
        unique_colors = set(colors)
        self.assertEqual(len(unique_colors), len(nets), "Not all nets received unique colors")

def run_visualization_tests():
    """Run the visualization test suite."""
    # Check if plotly is installed
    try:
        import plotly
        print("Running PCB visualization tests...")
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
    except ImportError:
        print("Plotly is not installed. Skipping 3D visualization tests.")
        print("To run these tests, install plotly: pip install plotly")

if __name__ == "__main__":
    run_visualization_tests() 