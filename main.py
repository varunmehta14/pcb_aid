# from trace_extractor_old import PCBTraceExtractor

# def print_differences(extractor):
#     test_cases = [
#         ("U1", "11", "R66", "1", 5.30688),
#         ("U1", "61", "C43", "2", 5.90118),
#         ("U1", "20", "C3", "2", 2.09999),
#         ("U1", "20", "R2", "1", 4.009),
#         ("U1", "9", "D5", "2", 9.97167),
#         ("R76", "1", "U1", "37", 40.3965),
#         ("U1", "4", "R54", "2", 26.30932),
#         ("R35", "2", "Q6", "4", 1.9921),
#         ("R32", "2", "Q6", "4", 4.8794),
#         ("U1", "22", "R17", "1", 10.1542),  # updated expected value
#         ("U1", "15", "C2", "1", 5.95187),
#         ("U1", "19", "R15", "1", 9.64036),
#         ("U1", "47", "C38", "2", 38.5496),
#         ("U1", "6", "C26", "1", 4.84104),
#         ("R2", "1", "C3", "2", 1.90922),
#         ("U1", "9", "C21", "2", 3.7029),
#         ("D8", "2", "D4", "2", 1.9909),
#         ("U1", "62", "C44", "1", 3.75556),
#         ("U1", "62", "R29", "1", 48.4302),
#     ]
    
#     for c1, p1, c2, p2, expected in test_cases:
#         actual = extractor.extract_traces_between_pads(c1, p1, c2, p2)
#         if actual is not None:
#             diff = abs(actual - expected)
#             status = "PASS" if diff < 0.1 else "FAIL"
#             print(f"{c1}.{p1} → {c2}.{p2}: Expected={expected}, Actual={actual:.5f}, Diff={diff:.5f}, {status}")
#         else:
#             print(f"{c1}.{p1} → {c2}.{p2}: Expected={expected}, Actual=None → FAIL")


# if __name__ == "__main__":
#     extractor = PCBTraceExtractor()
#     extractor.load_json_file("Vacuum_PCB_OBjects.json")
#     # print_differences(extractor)

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "11", "R66", "1") - 5.30688
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "61", "C43", "2") - 5.90118
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "20", "C3", "2") - 2.09999
#     ) < 0.1

#     # assert abs(
#     #     extractor.extract_traces_between_pads("U1", "20", "R2", "1") - 4.009
#     # ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "9", "D5", "2") - 9.97167
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("R76", "1", "U1", "37") - 40.3965
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "4", "R54", "2") - 26.30932
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("R35", "2", "Q6", "4") - 1.9921
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("R32", "2", "Q6", "4") - 4.8794
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "22", "R17", "1") - 10.1542
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "15", "C2", "1") - 5.95187
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "19", "R15", "1") - 9.64036
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "47", "C38", "2") - 38.5496
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "6", "C26", "1") - 4.84104
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("R2", "1", "C3", "2") - 1.90922
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "9", "C21", "2") - 3.7029
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("D8", "2", "D4", "2") - 1.9909
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "62", "C44", "1") - 3.75556
#     ) < 0.1

#     assert abs(
#         extractor.extract_traces_between_pads("U1", "62", "R29", "1") - 48.4302
#     ) < 0.1

#     assert extractor.extract_traces_between_pads("U1", "66", "C28", "2") is None

#     assert extractor.extract_traces_between_pads("U1", "65", "R85", "1") is None

#     assert extractor.extract_traces_between_pads("D8", "2", "R85", "1") is None

#     assert extractor.extract_traces_between_pads("U2", "2", "C9", "2") is None

#     assert extractor.extract_traces_between_pads("U1", "51", "R26", "2") is None

#     assert extractor.extract_traces_between_pads("D5", "1", "R37", "2") is None
# main.py
import argparse
# Ensure you are importing the correct, potentially modified, extractor
from trace_extractor import PCBTraceExtractor

# Default JSON file path (can be changed here if needed)
DEFAULT_JSON_FILE = "Vacuum_PCB_OBjects.json"

# Modify run_assertions to accept the debug flag
def run_assertions(json_file=DEFAULT_JSON_FILE, debug_mode=False):
    """Loads data and runs the predefined assertions, passing the debug flag."""
    print(f"\n--- Running Predefined Assertions using {json_file} (Debug Mode: {debug_mode}) ---")
    extractor = PCBTraceExtractor()
    try:
        extractor.load_json_file(json_file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file}' for assertions.")
        return False # Indicate failure
    except Exception as e:
        print(f"Error loading or parsing JSON file '{json_file}' for assertions: {e}")
        return False # Indicate failure

    if not extractor.objects:
        print("Error: No objects loaded for assertions.")
        return False # Indicate failure

    all_passed = True
    try:
        # Pass debug_mode to each extractor call within assertions
        assert abs(extractor.extract_traces_between_pads("U1", "11", "R66", "1", debug=debug_mode) - 5.30688) < 0.1, "Assertion U1.11-R66.1 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "61", "C43", "2", debug=debug_mode) - 5.90118) < 0.1, "Assertion U1.61-C43.2 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "20", "C3", "2", debug=debug_mode) - 2.09999) < 0.1, "Assertion U1.20-C3.2 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "20", "R2", "1", debug=debug_mode) - 4.009) < 0.1 # Example commented out
        assert abs(extractor.extract_traces_between_pads("U1", "9", "D5", "2", debug=debug_mode) - 9.97167) < 0.1, "Assertion U1.9-D5.2 failed"
        assert abs(extractor.extract_traces_between_pads("R76", "1", "U1", "37", debug=debug_mode) - 40.3965) < 0.1, "Assertion R76.1-U1.37 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "4", "R54", "2", debug=debug_mode) - 26.30932) < 0.1, "Assertion U1.4-R54.2 failed"
        assert abs(extractor.extract_traces_between_pads("R35", "2", "Q6", "4", debug=debug_mode) - 1.9921) < 0.1, "Assertion R35.2-Q6.4 failed"
        assert abs(extractor.extract_traces_between_pads("R32", "2", "Q6", "4", debug=debug_mode) - 4.8794) < 0.1, "Assertion R32.2-Q6.4 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "22", "R17", "1", debug=debug_mode) - 10.1542) < 0.1, "Assertion U1.22-R17.1 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "15", "C2", "1", debug=debug_mode) - 5.95187) < 0.1, "Assertion U1.15-C2.1 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "19", "R15", "1", debug=debug_mode) - 9.64036) < 0.1, "Assertion U1.19-R15.1 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "47", "C38", "2", debug=debug_mode) - 38.5496) < 0.1, "Assertion U1.47-C38.2 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "6", "C26", "1", debug=debug_mode) - 4.84104) < 0.1, "Assertion U1.6-C26.1 failed"
        assert abs(extractor.extract_traces_between_pads("R2", "1", "C3", "2", debug=debug_mode) - 1.90922) < 0.1, "Assertion R2.1-C3.2 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "9", "C21", "2", debug=debug_mode) - 3.7029) < 0.1, "Assertion U1.9-C21.2 failed"
        assert abs(extractor.extract_traces_between_pads("D8", "2", "D4", "2", debug=debug_mode) - 1.9909) < 0.1, "Assertion D8.2-D4.2 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "62", "C44", "1", debug=debug_mode) - 3.75556) < 0.1, "Assertion U1.62-C44.1 failed"
        assert abs(extractor.extract_traces_between_pads("U1", "62", "R29", "1", debug=debug_mode) - 48.4302) < 0.1, "Assertion U1.62-R29.1 failed"
        assert extractor.extract_traces_between_pads("U1", "66", "C28", "2", debug=debug_mode) is None, "Assertion U1.66-C28.2 (None) failed"
        assert extractor.extract_traces_between_pads("U1", "65", "R85", "1", debug=debug_mode) is None, "Assertion U1.65-R85.1 (None) failed"
        assert extractor.extract_traces_between_pads("D8", "2", "R85", "1", debug=debug_mode) is None, "Assertion D8.2-R85.1 (None) failed"
        assert extractor.extract_traces_between_pads("U2", "2", "C9", "2", debug=debug_mode) is None, "Assertion U2.2-C9.2 (None) failed"
        assert extractor.extract_traces_between_pads("U1", "51", "R26", "2", debug=debug_mode) is None, "Assertion U1.51-R26.2 (None) failed"
        assert extractor.extract_traces_between_pads("D5", "1", "R37", "2", debug=debug_mode) is None, "Assertion D5.1-R37.2 (None) failed"

    except AssertionError as e:
        print(f"Assertion Failed: {e}")
        all_passed = False
    except Exception as e:
        print(f"An error occurred during assertions: {e}")
        all_passed = False

    print("--- Assertions Complete ---")
    return all_passed


if __name__ == "__main__":
    # Check prerequisites first
    try:
        import networkx
        import shapely
    except ImportError:
        print("Error: Required libraries 'networkx' or 'shapely' not found.")
        print("Please install them using: pip install networkx shapely")
        exit(1) # Exit if libraries missing

    # Set up ArgumentParser for just the --debug flag
    parser = argparse.ArgumentParser(description='Run PCB trace extraction assertions.')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (prints detailed steps and path for all assertions).')

    # Parse the arguments
    args = parser.parse_args()

    # Always run the assertions, passing the parsed debug flag
    success = run_assertions(debug_mode=args.debug)

    # Optional: Exit with non-zero status if assertions failed
    if not success:
        print("\nOne or more assertions failed.")
        # exit(1) # Uncomment to make CI/scripts fail on assertion errors

    print("\nScript finished.")
