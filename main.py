#!/usr/bin/env python3
# main.py - Test script for PCB trace extraction
import argparse
import time
import sys
from trace_extractor import PCBTraceExtractor

# Default JSON file path
DEFAULT_JSON_FILE = "backend/Vacuum_PCB_Objects.json"

def run_assertions(json_file=DEFAULT_JSON_FILE, debug_mode=False, verbose=False):
    """Loads data and runs the predefined assertions, passing the debug flag."""
    print(f"\n--- Running Predefined Assertions using {json_file} (Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}' for assertions.")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}' for assertions: {e}")
        return False

    if not extractor.objects:
        print("Error: No objects loaded for assertions.")
        return False

    # Define all test cases
    test_cases = [
        ("U1", "11", "R66", "1", 5.30688),
        ("U1", "61", "C43", "2", 5.90118),
        ("U1", "20", "C3", "2", 2.09999),
        ("U1", "20", "R2", "1", 4.009),
        ("U1", "9", "D5", "2", 9.97167),
        ("R76", "1", "U1", "37", 40.3965),
        ("U1", "4", "R54", "2", 26.30932),
        ("R35", "2", "Q6", "4", 1.9921),
        ("R32", "2", "Q6", "4", 4.8794),
        ("U1", "22", "R17", "1", 10.1542),
        ("U1", "15", "C2", "1", 5.95187),
        ("U1", "19", "R15", "1", 9.64036),
        ("U1", "47", "C38", "2", 38.5496),
        ("U1", "6", "C26", "1", 4.84104),
        ("R2", "1", "C3", "2", 1.90922),
        ("U1", "9", "C21", "2", 3.7029),
        ("D8", "2", "D4", "2", 1.9909),
        ("U1", "62", "C44", "1", 3.75556),
        ("U1", "62", "R29", "1", 48.4302),
    ]
    
    # Test cases expected to return None (no valid path)
    null_test_cases = [
        ("U1", "66", "C28", "2"),
        ("U1", "65", "R85", "1"),
        ("D8", "2", "R85", "1"),
        ("U2", "2", "C9", "2"),
        ("U1", "51", "R26", "2"),
        ("D5", "1", "R37", "2"),
    ]

    all_passed = True
    passed_count = 0
    total_tests = len(test_cases) + len(null_test_cases)
    
    # Run the positive test cases (should find paths)
    for i, (c1, p1, c2, p2, expected) in enumerate(test_cases):
        start_time = time.time()
        test_id = f"{c1}.{p1} → {c2}.{p2}"
        
        try:
            actual = extractor.extract_traces_between_pads(c1, p1, c2, p2, debug=debug_mode)
            execution_time = time.time() - start_time
            
            if actual is not None:
                diff = abs(actual - expected)
                passed = diff < 0.1
                
                if passed:
                    passed_count += 1
                    result = "PASS"
                else:
                    all_passed = False
                    result = "FAIL"
                
                if verbose or not passed:
                    print(f"{test_id}: Expected={expected:.5f}, Actual={actual:.5f}, Diff={diff:.5f}, Time={execution_time:.3f}s → {result}")
            else:
                all_passed = False
                print(f"{test_id}: Expected={expected:.5f}, Actual=None, Time={execution_time:.3f}s → FAIL")
        except Exception as e:
            all_passed = False
            print(f"{test_id}: Expected={expected:.5f}, ERROR: {e} → FAIL")
    
    # Run the null test cases (should return None)
    for c1, p1, c2, p2 in null_test_cases:
        start_time = time.time()
        test_id = f"{c1}.{p1} → {c2}.{p2}"
        
        try:
            actual = extractor.extract_traces_between_pads(c1, p1, c2, p2, debug=debug_mode)
            execution_time = time.time() - start_time
            
            if actual is None:
                passed_count += 1
                if verbose:
                    print(f"{test_id}: Expected=None, Actual=None, Time={execution_time:.3f}s → PASS")
            else:
                all_passed = False
                print(f"{test_id}: Expected=None, Actual={actual:.5f}, Time={execution_time:.3f}s → FAIL")
        except Exception as e:
            all_passed = False
            print(f"{test_id}: Expected=None, ERROR: {e} → FAIL")
    
    # Print summary
    print(f"\nSummary: {passed_count}/{total_tests} tests passed ({passed_count/total_tests*100:.1f}%)")
    
    return all_passed


def run_custom_test(json_file, c1, p1, c2, p2, debug_mode=False):
    """Run a custom trace extraction test between specified pads."""
    print(f"\n--- Running Custom Test: {c1}.{p1} → {c2}.{p2} (Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    start_time = time.time()
    try:
        result = extractor.extract_traces_between_pads(c1, p1, c2, p2, debug=debug_mode)
        end_time = time.time()
        
        if result is not None:
            mm_result = result * 0.0254  # Convert mils to mm
            print(f"\nTrace length: {result:.5f} mils ({mm_result:.5f} mm)")
            print(f"Calculation time: {(end_time - start_time):.3f} seconds")
            return True
        else:
            print(f"\nNo trace found between {c1}.{p1} and {c2}.{p2}")
            print(f"Calculation time: {(end_time - start_time):.3f} seconds")
            return False
    except Exception as e:
        print(f"\nError calculating trace: {e}")
        return False


def analyze_net(json_file, net_name, debug_mode=False):
    """Print information about the extractor and perform a few trace measurements for demonstration."""
    print(f"\n--- Demonstrating Trace Extractor with Net: {net_name} (Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    # Test a few known good connections to see if they work
    test_cases = [
        # These values are based on known working tests from the assertions
        ("U1", "11", "R66", "1"),  # Short trace
        ("R76", "1", "U1", "37"),  # Medium trace
        ("U1", "62", "R29", "1"),  # Long trace
    ]
    
    print(f"\nPerforming sample measurements for demonstration:")
    for i, (c1, p1, c2, p2) in enumerate(test_cases, 1):
        start_time = time.time()
        try:
            result = extractor.extract_traces_between_pads(c1, p1, c2, p2, debug=debug_mode)
            end_time = time.time()
            
            if result is not None:
                mm_result = result * 0.0254  # Convert mils to mm
                print(f"  {i}. {c1}.{p1} → {c2}.{p2}: {result:.5f} mils ({mm_result:.5f} mm) [{(end_time - start_time):.3f}s]")
            else:
                print(f"  {i}. {c1}.{p1} → {c2}.{p2}: No trace found [{(end_time - start_time):.3f}s]")
        except Exception as e:
            print(f"  {i}. {c1}.{p1} → {c2}.{p2}: Error: {e}")
    
    return True


def run_performance_test(json_file, iterations=3, debug_mode=False):
    """Run a performance test by executing all test cases multiple times."""
    print(f"\n--- Running Performance Test ({iterations} iterations) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    # Define all test cases
    test_cases = [
        ("U1", "11", "R66", "1", 5.30688),
        ("U1", "61", "C43", "2", 5.90118),
        ("U1", "20", "C3", "2", 2.09999),
        ("U1", "20", "R2", "1", 4.009),
        ("U1", "9", "D5", "2", 9.97167),
        ("R76", "1", "U1", "37", 40.3965),
        ("U1", "4", "R54", "2", 26.30932),
        ("R35", "2", "Q6", "4", 1.9921),
        ("R32", "2", "Q6", "4", 4.8794),
        ("U1", "22", "R17", "1", 10.1542),
        ("U1", "15", "C2", "1", 5.95187),
        ("U1", "19", "R15", "1", 9.64036),
        ("U1", "47", "C38", "2", 38.5496),
        ("U1", "6", "C26", "1", 4.84104),
        ("R2", "1", "C3", "2", 1.90922),
        ("U1", "9", "C21", "2", 3.7029),
        ("D8", "2", "D4", "2", 1.9909),
        ("U1", "62", "C44", "1", 3.75556),
        ("U1", "62", "R29", "1", 48.4302),
    ]
    
    # Also include a few negative cases
    null_test_cases = [
        ("U1", "66", "C28", "2", None),
        ("U1", "65", "R85", "1", None),
        ("D8", "2", "R85", "1", None),
    ]
    
    # Combine all test cases
    all_test_cases = test_cases + null_test_cases
    
    # Dictionary to store timing results
    results = {}
    
    # Run all test cases multiple times
    for iteration in range(iterations):
        print(f"\nIteration {iteration + 1}/{iterations}")
        
        for idx, test_case in enumerate(all_test_cases):
            c1, p1, c2, p2 = test_case[0], test_case[1], test_case[2], test_case[3]
            expected = test_case[4]
            test_id = f"{c1}.{p1} → {c2}.{p2}"
            
            start_time = time.time()
            try:
                actual = extractor.extract_traces_between_pads(c1, p1, c2, p2, debug=False)  # Always disable debug for performance test
                execution_time = time.time() - start_time
                
                # Initialize results dict entry if it doesn't exist
                if test_id not in results:
                    results[test_id] = {
                        'expected': expected,
                        'times': [],
                        'values': [],
                        'successes': 0,
                        'failures': 0
                    }
                
                # Store timing and result
                results[test_id]['times'].append(execution_time)
                results[test_id]['values'].append(actual)
                
                # Check if result is correct
                if expected is None:
                    if actual is None:
                        results[test_id]['successes'] += 1
                    else:
                        results[test_id]['failures'] += 1
                else:
                    if actual is not None and abs(actual - expected) < 0.1:
                        results[test_id]['successes'] += 1
                    else:
                        results[test_id]['failures'] += 1
                
                # Print progress indicator
                if iteration == 0:
                    print(f"  {idx+1}/{len(all_test_cases)}: {test_id} - {execution_time:.3f}s", end="\r")
                
            except Exception as e:
                # Handle errors
                if test_id not in results:
                    results[test_id] = {
                        'expected': expected,
                        'times': [],
                        'values': [],
                        'successes': 0,
                        'failures': 0,
                        'errors': []
                    }
                results[test_id]['failures'] += 1
                if 'errors' not in results[test_id]:
                    results[test_id]['errors'] = []
                results[test_id]['errors'].append(str(e))
                results[test_id]['times'].append(execution_time)
                results[test_id]['values'].append(None)
    
    # Calculate and print statistics
    print("\n\nPerformance Results:")
    print(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    print(f"{'Test Case':<20} | {'Avg (ms)':<10} | {'Min (ms)':<10} | {'Max (ms)':<10} | {'Success':<10} | {'Result':<10}")
    
    total_time = 0
    total_success_rate = 0
    
    for test_id, data in results.items():
        if not data['times']:
            continue
            
        # Calculate statistics
        avg_time = sum(data['times']) / len(data['times']) * 1000  # Convert to ms
        min_time = min(data['times']) * 1000
        max_time = max(data['times']) * 1000
        success_rate = data['successes'] / (data['successes'] + data['failures']) * 100
        
        # Determine result consistency
        values = [v for v in data['values'] if v is not None]
        if not values:
            result = "N/A"
        elif len(values) <= 1:
            result = f"{values[0]:.5f}" if values else "N/A"
        else:
            min_val = min(values)
            max_val = max(values)
            if abs(max_val - min_val) < 0.001:
                result = f"{values[0]:.5f}"
            else:
                result = f"{min_val:.5f}-{max_val:.5f}"
        
        # Print row
        print(f"{test_id:<20} | {avg_time:10.2f} | {min_time:10.2f} | {max_time:10.2f} | {success_rate:9.1f}% | {result:<10}")
        
        total_time += avg_time
        total_success_rate += success_rate
    
    # Print summary
    num_tests = len(results)
    avg_success_rate = total_success_rate / num_tests if num_tests > 0 else 0
    print(f"\nSummary:")
    print(f"  Total tests: {num_tests}")
    print(f"  Avg. success rate: {avg_success_rate:.2f}%")
    print(f"  Total avg. execution time: {total_time:.2f} ms")
    
    return True


def test_multi_net_analysis(json_file, component1, pad1, component2, pad2, debug_mode=False, timeout=30):
    """Test multi-net path analysis between components that might cross multiple nets."""
    print(f"\n--- Testing Multi-Net Analysis: {component1}.{pad1} → {component2}.{pad2} (Debug Mode: {debug_mode}, Timeout: {timeout}s) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    start_time = time.time()
    
    # Define a timeout handler
    def timeout_handler(signum, frame):
        raise TimeoutError("Analysis took too long and was terminated")
        
    # Set up the timeout if supported by the platform
    try:
        import signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        timeout_enabled = True
    except (ImportError, AttributeError):
        print("Warning: Timeout functionality not available on this platform.")
        timeout_enabled = False
        
    try:
        # Use the exact method signature: (start_comp, start_pad, end_comp, end_pad, jumper_points=None)
        result = extractor.analyze_multi_net_path(component1, pad1, component2, pad2)
            
        # Cancel the timeout if it was set
        if timeout_enabled:
            signal.alarm(0)
            
        end_time = time.time()
        
        if result and 'complete_path' in result and result['complete_path']:
            # Path found through multiple nets
            print(f"\nMulti-net path found between {component1}.{pad1} and {component2}.{pad2}")
            print(f"Total path length: {result['total_length_mils']:.5f} mils ({result['total_length_mm']:.5f} mm)")
            print(f"Nets traversed: {', '.join(result['nets_traversed'])}")
            print(f"Calculation time: {(end_time - start_time):.3f} seconds")
            
            # Print path segments
            if 'path_segments' in result:
                print("\nPath segments:")
                for i, segment in enumerate(result['path_segments'], 1):
                    net = segment.get('net', 'Unknown')
                    length = segment.get('length_mils', 0)
                    start = segment.get('start_point', {})
                    end = segment.get('end_point', {})
                    print(f"  {i}. Net: {net}, Length: {length:.5f} mils")
                    print(f"     From: {start.get('component', '?')}.{start.get('pad', '?')}")
                    print(f"     To: {end.get('component', '?')}.{end.get('pad', '?')}")
            
            return True
        else:
            print(f"\nNo multi-net path found between {component1}.{pad1} and {component2}.{pad2}")
            print(f"Calculation time: {(end_time - start_time):.3f} seconds")
            return False
    except TimeoutError as e:
        print(f"\n{e}")
        print(f"The multi-net analysis took longer than {timeout} seconds and was terminated.")
        return False
    except AttributeError:
        # Cancel the timeout if it was set
        if timeout_enabled:
            signal.alarm(0)
        print(f"\nFunction 'analyze_multi_net_path' not implemented in the trace extractor.")
        return False
    except Exception as e:
        # Cancel the timeout if it was set
        if timeout_enabled:
            signal.alarm(0)
        print(f"\nError during multi-net analysis: {e}")
        return False
    finally:
        # Make sure to cancel the timeout
        if timeout_enabled:
            signal.alarm(0)


def test_impedance_calculation(json_file, component1, pad1, component2, pad2, debug_mode=False):
    """Test trace impedance calculation between two pads."""
    print(f"\n--- Testing Impedance Calculation: {component1}.{pad1} → {component2}.{pad2} (Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    start_time = time.time()
    try:
        # First check if there's a trace between these pads
        trace_length = extractor.extract_traces_between_pads(component1, pad1, component2, pad2, debug=False)
        
        if trace_length is None:
            print(f"\nNo trace found between {component1}.{pad1} and {component2}.{pad2}, cannot calculate impedance.")
            return False
            
        # Try to calculate impedance
        try:
            # First try with debug parameter
            impedance_result = extractor.calculate_trace_impedance(component1, pad1, component2, pad2, debug=debug_mode)
        except TypeError:
            # If it fails, try without the debug parameter
            print("Trying alternative method signature...")
            impedance_result = extractor.calculate_trace_impedance(component1, pad1, component2, pad2)
            
        end_time = time.time()
        
        if impedance_result:
            print(f"\nImpedance calculation successful:")
            print(f"Trace length: {trace_length:.5f} mils ({trace_length * 0.0254:.5f} mm)")
            print(f"Characteristic impedance: {impedance_result.get('impedance_ohms', 0):.2f} Ohms")
            
            # Print additional impedance parameters if available
            if 'trace_width' in impedance_result:
                print(f"Trace width: {impedance_result['trace_width']:.5f} mils")
            if 'dielectric_constant' in impedance_result:
                print(f"Dielectric constant: {impedance_result['dielectric_constant']:.2f}")
            if 'dielectric_thickness' in impedance_result:
                print(f"Dielectric thickness: {impedance_result['dielectric_thickness']:.5f} mils")
            if 'copper_thickness' in impedance_result:
                print(f"Copper thickness: {impedance_result['copper_thickness']:.5f} mils")
                
            print(f"Calculation time: {(end_time - start_time):.3f} seconds")
            return True
        else:
            print(f"\nImpedance calculation failed for trace between {component1}.{pad1} and {component2}.{pad2}")
            print(f"Calculation time: {(end_time - start_time):.3f} seconds")
            return False
    except AttributeError:
        print(f"\nFunction 'calculate_trace_impedance' not implemented in the trace extractor.")
        return False
    except Exception as e:
        print(f"\nError during impedance calculation: {e}")
        return False


def test_3d_visualization(json_file, net_name, output_file=None, debug_mode=False):
    """Test 3D PCB visualization generation."""
    if output_file is None:
        output_file = f"{net_name}_3d_view.html"
        
    print(f"\n--- Testing 3D Visualization (Output: {output_file}, Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    # Note: The method does not accept a net_name parameter according to the signature
    # We include it in our function for possible future use
    print(f"Note: The generate_3d_visualization method doesn't accept a net parameter.")
    print(f"It will visualize all nets or use its own selection logic.")
    
    start_time = time.time()
    try:
        # Use the exact method signature: (output_file=None)
        print(f"Generating 3D visualization to '{output_file}'...")
        result = extractor.generate_3d_visualization(output_file)
            
        end_time = time.time()
        
        if result:
            print(f"\n3D visualization successfully generated:")
            print(f"Output file: {output_file}")
            print(f"Generation time: {(end_time - start_time):.3f} seconds")
            return True
        else:
            print(f"\nFailed to generate 3D visualization")
            print(f"Generation time: {(end_time - start_time):.3f} seconds")
            return False
    except AttributeError:
        print(f"\nFunction 'generate_3d_visualization' not implemented in the trace extractor.")
        return False
    except Exception as e:
        print(f"\nError during 3D visualization generation: {e}")
        return False


def test_eda_integration(json_file, eda_format="altium", output_file=None, debug_mode=False):
    """Test integration with EDA tools by exporting/importing trace data."""
    if output_file is None:
        output_file = f"eda_export.{eda_format}"
        
    print(f"\n--- Testing EDA Integration: Export to {eda_format.upper()} format (Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    start_time = time.time()
    try:
        # Try to export data to EDA format
        try:
            # First try with debug parameter
            result = extractor.export_to_eda_format(eda_format, output_file, debug=debug_mode)
        except TypeError:
            # If it fails, try without the debug parameter
            print("Trying alternative method signature...")
            result = extractor.export_to_eda_format(eda_format, output_file)
            
        end_time = time.time()
        
        if result:
            print(f"\nSuccessfully exported PCB data to {eda_format.upper()} format:")
            print(f"Output file: {output_file}")
            print(f"Export time: {(end_time - start_time):.3f} seconds")
            
            # If applicable, also test import
            try:
                start_time = time.time()
                try:
                    # First try with debug parameter
                    import_result = extractor.import_from_eda_format(output_file, eda_format, debug=debug_mode)
                except TypeError:
                    # If it fails, try without the debug parameter
                    import_result = extractor.import_from_eda_format(output_file, eda_format)
                end_time = time.time()
                
                if import_result:
                    print(f"\nSuccessfully re-imported PCB data from {eda_format.upper()} format")
                    print(f"Import time: {(end_time - start_time):.3f} seconds")
                else:
                    print(f"\nFailed to re-import PCB data from {eda_format.upper()} format")
            except (AttributeError, Exception) as e:
                # Import functionality might not be implemented, so don't fail the test
                print(f"\nNote: Import from EDA format not tested: {str(e)}")
                
            return True
        else:
            print(f"\nFailed to export PCB data to {eda_format.upper()} format")
            print(f"Operation time: {(end_time - start_time):.3f} seconds")
            return False
    except AttributeError:
        print(f"\nFunction 'export_to_eda_format' not implemented in the trace extractor.")
        return False
    except Exception as e:
        print(f"\nError during EDA format export: {e}")
        return False


def check_advanced_features(json_file, debug_mode=False):
    """Check which advanced features are implemented in the trace extractor."""
    print(f"\n--- Checking Advanced Features in PCB Trace Extractor ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
        print(f"Successfully loaded PCB data from {json_file}")
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}'")
        return False
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}': {e}")
        return False

    implemented_features = []
    missing_features = []
    
    # Check for known good test cases from assertions
    test_case = ("U1", "11", "R66", "1")
    
    # 1. Check basic trace extraction (should be implemented)
    print("\n1. Basic Trace Extraction")
    try:
        result = extractor.extract_traces_between_pads(*test_case)
        if result is not None:
            print(f"  ✅ Basic trace extraction: {result:.5f} mils")
            implemented_features.append("Basic trace extraction")
        else:
            print(f"  ❌ Basic trace extraction: No path found")
            missing_features.append("Basic trace extraction")
    except Exception as e:
        print(f"  ❌ Basic trace extraction: Error - {e}")
        missing_features.append("Basic trace extraction")
        
    # 2. Check multi-net path analysis
    print("\n2. Multi-Net Path Analysis")
    try:
        # Check if the method exists first
        if hasattr(extractor, 'analyze_multi_net_path'):
            print(f"  ✅ Method 'analyze_multi_net_path' is implemented")
            # Try to get its signature
            import inspect
            try:
                sig = inspect.signature(extractor.analyze_multi_net_path)
                print(f"     Signature: {sig}")
            except Exception:
                pass
            implemented_features.append("Multi-net path analysis")
        else:
            print(f"  ❌ Method 'analyze_multi_net_path' is NOT implemented")
            missing_features.append("Multi-net path analysis")
    except Exception as e:
        print(f"  ❌ Multi-net path analysis check failed: {e}")
        missing_features.append("Multi-net path analysis")
        
    # 3. Check impedance calculation
    print("\n3. Trace Impedance Calculation")
    try:
        if hasattr(extractor, 'calculate_trace_impedance'):
            print(f"  ✅ Method 'calculate_trace_impedance' is implemented")
            implemented_features.append("Impedance calculation")
        else:
            print(f"  ❌ Method 'calculate_trace_impedance' is NOT implemented")
            missing_features.append("Impedance calculation")
    except Exception as e:
        print(f"  ❌ Impedance calculation check failed: {e}")
        missing_features.append("Impedance calculation")
        
    # 4. Check 3D visualization
    print("\n4. 3D PCB Visualization")
    try:
        if hasattr(extractor, 'generate_3d_visualization'):
            print(f"  ✅ Method 'generate_3d_visualization' is implemented")
            # Try to get its signature
            import inspect
            try:
                sig = inspect.signature(extractor.generate_3d_visualization)
                print(f"     Signature: {sig}")
            except Exception:
                pass
            implemented_features.append("3D visualization")
        else:
            print(f"  ❌ Method 'generate_3d_visualization' is NOT implemented")
            missing_features.append("3D visualization")
    except Exception as e:
        print(f"  ❌ 3D visualization check failed: {e}")
        missing_features.append("3D visualization")
        
    # 5. Check EDA integration (export)
    print("\n5. EDA Tool Integration (Export)")
    try:
        if hasattr(extractor, 'export_to_eda_format'):
            print(f"  ✅ Method 'export_to_eda_format' is implemented")
            implemented_features.append("EDA export")
        else:
            print(f"  ❌ Method 'export_to_eda_format' is NOT implemented")
            missing_features.append("EDA export")
    except Exception as e:
        print(f"  ❌ EDA export check failed: {e}")
        missing_features.append("EDA export")
        
    # 6. Check EDA integration (import)
    print("\n6. EDA Tool Integration (Import)")
    try:
        if hasattr(extractor, 'import_from_eda_format'):
            print(f"  ✅ Method 'import_from_eda_format' is implemented")
            implemented_features.append("EDA import")
        else:
            print(f"  ❌ Method 'import_from_eda_format' is NOT implemented")
            missing_features.append("EDA import")
    except Exception as e:
        print(f"  ❌ EDA import check failed: {e}")
        missing_features.append("EDA import")
        
    # Summary
    print("\n--- Advanced Features Summary ---")
    print(f"Implemented features ({len(implemented_features)}):")
    for feature in implemented_features:
        print(f"  ✅ {feature}")
        
    print(f"\nMissing features ({len(missing_features)}):")
    for feature in missing_features:
        print(f"  ❌ {feature}")
        
    # Overall status
    if implemented_features:
        print("\nSome advanced features are implemented in the trace extractor.")
        return True
    else:
        print("\nNo advanced features are implemented in the trace extractor.")
        return False


if __name__ == "__main__":
    # Check prerequisites first
    try:
        import networkx
        import shapely
    except ImportError as e:
        print(f"Error: Required library not found - {e}")
        print("Please install required libraries using: pip install networkx shapely")
        exit(1)

    # Set up ArgumentParser
    parser = argparse.ArgumentParser(description='PCB Trace Extraction Test Suite')
    parser.add_argument('--json', type=str, default=DEFAULT_JSON_FILE,
                      help=f'Path to PCB JSON file (default: {DEFAULT_JSON_FILE})')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode (prints detailed extraction steps)')
    parser.add_argument('--verbose', action='store_true',
                      help='Show all test results, not just failures')
    
    # Add subparsers for different test modes
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # "test" command - run all assertions
    test_parser = subparsers.add_parser('test', help='Run all assertions')
    
    # "custom" command - measure a specific connection
    custom_parser = subparsers.add_parser('custom', help='Measure a specific connection')
    custom_parser.add_argument('component1', help='First component designator')
    custom_parser.add_argument('pad1', help='First pad number')
    custom_parser.add_argument('component2', help='Second component designator')
    custom_parser.add_argument('pad2', help='Second pad number')
    
    # "analyze" command - analyze a specific net
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a specific net')
    analyze_parser.add_argument('net', help='Net name to analyze')

    # "performance" command - run performance test
    performance_parser = subparsers.add_parser('performance', help='Run performance test')
    performance_parser.add_argument('--iterations', type=int, default=3,
                                   help='Number of iterations for performance test')
                                   
    # "multi-net" command - test multi-net path analysis
    multi_net_parser = subparsers.add_parser('multi-net', help='Test multi-net path analysis')
    multi_net_parser.add_argument('component1', help='First component designator')
    multi_net_parser.add_argument('pad1', help='First pad number')
    multi_net_parser.add_argument('component2', help='Second component designator')
    multi_net_parser.add_argument('pad2', help='Second pad number')
    multi_net_parser.add_argument('--timeout', type=int, default=30,
                                help='Timeout in seconds (default: 30)')
                                
    # "impedance" command - test impedance calculation
    impedance_parser = subparsers.add_parser('impedance', help='Test trace impedance calculation')
    impedance_parser.add_argument('component1', help='First component designator')
    impedance_parser.add_argument('pad1', help='First pad number')
    impedance_parser.add_argument('component2', help='Second component designator')
    impedance_parser.add_argument('pad2', help='Second pad number')
    
    # "3d-vis" command - test 3D visualization
    vis_parser = subparsers.add_parser('3d-vis', help='Test 3D PCB visualization')
    vis_parser.add_argument('--net', help='Net name for reference (note: implementation may not use this)')
    vis_parser.add_argument('--output', help='Output HTML file path (default: visualization.html)')
    
    # "eda" command - test EDA tool integration
    eda_parser = subparsers.add_parser('eda', help='Test EDA tool integration')
    eda_parser.add_argument('--format', choices=['altium', 'kicad', 'eagle'], default='altium',
                          help='EDA format to export/import (default: altium)')
    eda_parser.add_argument('--output', help='Output file path')

    # "check-features" command - check which advanced features are implemented
    features_parser = subparsers.add_parser('check-features', help='Check which advanced features are implemented')

    # Parse arguments
    args = parser.parse_args()
    
    # If no command specified, default to 'test'
    if not args.command:
        args.command = 'test'
    
    # Execute the appropriate command
    if args.command == 'test':
        success = run_assertions(json_file=args.json, debug_mode=args.debug, verbose=args.verbose)
        if not success:
            print("\nOne or more assertions failed.")
            sys.exit(1)
            
    elif args.command == 'custom':
        success = run_custom_test(args.json, 
                                 args.component1, args.pad1, 
                                 args.component2, args.pad2, 
                                 debug_mode=args.debug)
        if not success:
            sys.exit(1)
            
    elif args.command == 'analyze':
        success = analyze_net(args.json, args.net, debug_mode=args.debug)
        if not success:
            sys.exit(1)
            
    elif args.command == 'performance':
        success = run_performance_test(args.json, iterations=args.iterations, debug_mode=args.debug)
        if not success:
            sys.exit(1)
            
    elif args.command == 'multi-net':
        success = test_multi_net_analysis(args.json,
                                        args.component1, args.pad1,
                                        args.component2, args.pad2,
                                        debug_mode=args.debug,
                                        timeout=args.timeout)
        if not success:
            sys.exit(1)
            
    elif args.command == 'impedance':
        success = test_impedance_calculation(args.json,
                                           args.component1, args.pad1,
                                           args.component2, args.pad2,
                                           debug_mode=args.debug)
        if not success:
            sys.exit(1)
            
    elif args.command == '3d-vis':
        net_name = args.net if args.net else "ALL"
        output_file = args.output if args.output else "visualization.html"
        success = test_3d_visualization(args.json, net_name, output_file, debug_mode=args.debug)
        if not success:
            sys.exit(1)
            
    elif args.command == 'eda':
        success = test_eda_integration(args.json, args.format, args.output, debug_mode=args.debug)
        if not success:
            sys.exit(1)
            
    elif args.command == 'check-features':
        success = check_advanced_features(args.json, debug_mode=args.debug)
        if not success:
            sys.exit(1)
    
    print("\nScript finished successfully.")
