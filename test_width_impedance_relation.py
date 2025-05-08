import json
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from trace_extractor import PCBTraceExtractor, PCBLayer, PCBStackup, Track

def test_width_impedance_relation():
    """Test the relationship between trace width and impedance."""
    # First, verify if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        plotting_available = True
    except ImportError:
        plotting_available = False
        print("matplotlib not available - will only print numerical results")
    
    # Range of trace widths to test (in mils)
    widths = [4, 5, 6, 7, 8, 10, 12, 15, 20, 25, 30]
    
    # Create an extractor and set up a default stackup
    extractor = PCBTraceExtractor()
    
    # Create the default stackup
    default_layers = [
        PCBLayer("Top", 1, 6.0, "copper", 4.2),          # Top copper
        PCBLayer("Dielectric1", 2, 10.0, "FR4", 4.5),    # FR4 
        PCBLayer("GND", 3, 1.4, "copper", 1.0),          # GND plane
        PCBLayer("Dielectric2", 4, 10.0, "FR4", 4.5),    # FR4
        PCBLayer("Power", 5, 1.4, "copper", 1.0),        # Power plane
        PCBLayer("Dielectric3", 6, 10.0, "FR4", 4.5),    # FR4
        PCBLayer("Bottom", 7, 6.0, "copper", 4.2)        # Bottom copper
    ]
    stackup = PCBStackup(default_layers)
    
    # Calculate impedance for different trace widths
    microstrip_impedances = []
    stripline_impedances = []
    
    print("\n=== Trace Width vs. Impedance ===")
    print("Width (mils) | Microstrip (Ω) | Stripline (Ω)")
    print("-------------|----------------|-------------")
    
    for width in widths:
        # Create test tracks
        microstrip_track = Track(
            start=(0, 0),
            end=(100, 0),
            net_name="TEST",
            layer=1,  # Top layer
            length=100
        )
        microstrip_track.width = width
        
        stripline_track = Track(
            start=(0, 0),
            end=(100, 0),
            net_name="TEST",
            layer=4,  # Inner layer
            length=100
        )
        stripline_track.width = width
        
        # Calculate impedance
        microstrip_z = extractor.calculate_microstrip_impedance(microstrip_track, stackup)
        stripline_z = extractor.calculate_stripline_impedance(stripline_track, stackup)
        
        # Store results
        microstrip_impedances.append(microstrip_z)
        stripline_impedances.append(stripline_z)
        
        # Print results
        print(f"{width:11.1f} | {microstrip_z:14.2f} | {stripline_z:13.2f}")
    
    # Generate plots if matplotlib is available
    if plotting_available:
        plt.figure(figsize=(10, 6))
        plt.plot(widths, microstrip_impedances, 'b-o', label='Microstrip')
        plt.plot(widths, stripline_impedances, 'r-s', label='Stripline')
        plt.xlabel('Trace Width (mils)')
        plt.ylabel('Impedance (Ω)')
        plt.title('Trace Width vs. Impedance')
        plt.grid(True)
        plt.legend()
        
        # Save the plot
        plt.savefig('width_impedance_relation.png')
        print("\nPlot saved as 'width_impedance_relation.png'")
        
        # Generate additional plots for different dielectric heights
        dielectric_heights = [5.0, 7.5, 10.0, 12.5, 15.0]
        plt.figure(figsize=(10, 6))
        
        for height in dielectric_heights:
            # Update the dielectric layer height
            default_layers[1].height = height  # Dielectric1 height
            
            # Recalculate impedances
            height_impedances = []
            for width in widths:
                microstrip_track = Track(
                    start=(0, 0),
                    end=(100, 0),
                    net_name="TEST",
                    layer=1,
                    length=100
                )
                microstrip_track.width = width
                
                z = extractor.calculate_microstrip_impedance(microstrip_track, stackup)
                height_impedances.append(z)
            
            plt.plot(widths, height_impedances, '-o', label=f'Height={height} mils')
        
        plt.xlabel('Trace Width (mils)')
        plt.ylabel('Microstrip Impedance (Ω)')
        plt.title('Microstrip Impedance vs. Width for Different Dielectric Heights')
        plt.grid(True)
        plt.legend()
        
        # Save the plot
        plt.savefig('height_width_impedance_relation.png')
        print("Plot saved as 'height_width_impedance_relation.png'")
        
    # Generate a function to estimate target width for a given impedance
    # This uses a simple curve fit based on our data
    print("\n=== Trace Width Estimation ===")
    print("For target impedance of 50Ω:")
    
    # Use numpy's polyfit to create a simple curve fit function
    try:
        import numpy as np
        # For microstrip
        microstrip_coeffs = np.polyfit(microstrip_impedances, widths, 2)
        microstrip_poly = np.poly1d(microstrip_coeffs)
        microstrip_width_for_50ohm = microstrip_poly(50)
        
        # For stripline
        stripline_coeffs = np.polyfit(stripline_impedances, widths, 2)
        stripline_poly = np.poly1d(stripline_coeffs)
        stripline_width_for_50ohm = stripline_poly(50)
        
        print(f"Estimated microstrip width for 50Ω: {microstrip_width_for_50ohm:.2f} mils")
        print(f"Estimated stripline width for 50Ω: {stripline_width_for_50ohm:.2f} mils")
    except (ImportError, np.linalg.LinAlgError):
        print("Could not perform curve fitting (numpy might not be available or data points are not suitable)")

if __name__ == "__main__":
    test_width_impedance_relation() 