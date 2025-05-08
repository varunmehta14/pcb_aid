from typing import Dict, List, Optional
from langchain.tools import BaseTool
import sys
import os

# Add the parent directory to system path to allow importing trace_extractor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from trace_extractor import PCBTraceExtractor
from ..config import TRACE_LENGTH_THRESHOLD, COMPONENT_COUNT_THRESHOLD

class PCBAnalysisTool(BaseTool):
    # Remove class attributes and use hardcoded values in __init__
    
    def __init__(self, pcb_data: Dict, **kwargs):
        # Use hardcoded values
        kwargs["name"] = "pcb_analysis"
        kwargs["description"] = "Analyzes PCB layout and provides insights about trace lengths, critical paths, and design issues"
        
        super().__init__(**kwargs)
        print(f"PCBAnalysisTool initialized with pcb_data of type: {type(pcb_data)}")
        print(f"PCB data keys: {pcb_data.keys() if isinstance(pcb_data, dict) else 'Not a dict'}")
        object.__setattr__(self, "__extractor", PCBTraceExtractor(pcb_data))
    
    @property
    def extractor(self):
        return object.__getattribute__(self, "__extractor")
    
    def _run(self, query: str) -> str:
        """Run the tool with a natural language query about the PCB."""
        try:
            # Extract key information from the query
            if "trace length" in query.lower():
                return self._analyze_trace_lengths()
            elif "critical path" in query.lower():
                return self._analyze_critical_paths()
            elif "design issue" in query.lower():
                return self._analyze_design_issues()
            else:
                return "I can help analyze trace lengths, critical paths, and design issues. Please specify what you'd like to know."
        except Exception as e:
            # Return a helpful error message if something goes wrong
            return f"Error performing PCB analysis: {str(e)}. Please check if the PCB data is valid."
    
    def _analyze_trace_lengths(self) -> str:
        """Analyze trace lengths in the PCB."""
        nets = self.extractor.get_nets()
        analysis = []
        
        for net in nets:
            net_name = net["net_name"]
            component_count = net["component_count"]
            pad_count = net["pad_count"]
            
            analysis.append(f"Net {net_name}:")
            analysis.append(f"- Components: {component_count}")
            analysis.append(f"- Pads: {pad_count}")
            
            # Get trace lengths for this net
            traces = self.extractor.calculate_trace_lengths(net_name)
            if traces:
                analysis.append("Trace lengths:")
                for trace in traces:
                    analysis.append(f"- {trace['start_component']} to {trace['end_component']}: {trace['length_mm']:.2f}mm")
            
            analysis.append("")
        
        return "\n".join(analysis)
    
    def _analyze_critical_paths(self) -> str:
        """Analyze critical paths in the PCB."""
        nets = self.extractor.get_nets()
        critical_paths = []
        
        for net in nets:
            net_name = net["net_name"]
            traces = self.extractor.calculate_trace_lengths(net_name)
            
            if traces:
                # Find the longest trace in each net
                longest_trace = max(traces, key=lambda x: x["length_mm"])
                if longest_trace["length_mm"] > TRACE_LENGTH_THRESHOLD:
                    critical_paths.append({
                        "net": net_name,
                        "trace": longest_trace,
                        "reason": f"Trace length exceeds {TRACE_LENGTH_THRESHOLD}mm"
                    })
        
        if not critical_paths:
            return "No critical paths found in the current design."
        
        analysis = ["Critical Paths Analysis:"]
        for path in critical_paths:
            analysis.append(f"\nNet: {path['net']}")
            analysis.append(f"Longest Trace: {path['trace']['start_component']} to {path['trace']['end_component']}")
            analysis.append(f"Length: {path['trace']['length_mm']:.2f}mm")
            analysis.append(f"Issue: {path['reason']}")
        
        return "\n".join(analysis)
    
    def _analyze_design_issues(self) -> str:
        """Analyze potential design issues in the PCB."""
        issues = []
        
        # Check for nets with too many components
        nets = self.extractor.get_nets()
        for net in nets:
            if net["component_count"] > COMPONENT_COUNT_THRESHOLD:
                issues.append(f"Net {net['net_name']} has {net['component_count']} components, which might be too many for optimal routing")
        
        # Check for long traces
        for net in nets:
            traces = self.extractor.calculate_trace_lengths(net["net_name"])
            if traces:
                long_traces = [t for t in traces if t["length_mm"] > TRACE_LENGTH_THRESHOLD]
                if long_traces:
                    issues.append(f"Net {net['net_name']} has {len(long_traces)} traces longer than {TRACE_LENGTH_THRESHOLD}mm")
        
        if not issues:
            return "No significant design issues found in the current layout."
        
        return "Design Issues Found:\n" + "\n".join(f"- {issue}" for issue in issues) 