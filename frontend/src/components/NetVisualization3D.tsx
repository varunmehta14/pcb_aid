import React, { useState, useEffect } from 'react';
import { Box, Text, Spinner, Center, Heading, useToast } from '@chakra-ui/react';
import Plot from 'react-plotly.js';

interface NetVisualization3DProps {
  boardId: string;
  selectedNet: string;
}

const NetVisualization3D: React.FC<NetVisualization3DProps> = ({ boardId, selectedNet }) => {
  const [loading, setLoading] = useState<boolean>(false);
  // Store the figure spec (data and layout) from the API
  const [figureSpec, setFigureSpec] = useState<{ data: any[]; layout: any } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    if (!boardId || !selectedNet) {
      setFigureSpec(null); // Clear previous plot if boardId or selectedNet is missing
      return;
    }

    const fetchVisualizationData = async () => {
      setLoading(true);
      setError(null);
      setFigureSpec(null);
      try {
        // Construct the API URL dynamically
        // Assuming your backend is running on localhost:8000 (default for uvicorn in main.py)
        const apiUrl =  'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/boards/${boardId}/nets/${selectedNet}/visualize3d_data`);
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(`Failed to fetch 3D visualization data: ${errorData.detail || response.statusText}`);
        }
        
        const data = await response.json(); // This should be the Plotly figure spec (data and layout)
        setFigureSpec(data);

      } catch (err) {
        console.error("Error fetching 3D visualization data:", err);
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        setError(errorMessage);
        toast({
          title: 'Error Loading 3D Plot',
          description: errorMessage,
          status: 'error',
          duration: 7000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchVisualizationData();
  }, [boardId, selectedNet, toast]);

  if (!selectedNet) {
    return (
      <Center minH="500px">
        <Text>Please select a net to visualize in 3D.</Text>
      </Center>
    );
  }

  if (loading) {
    return (
      <Center minH="500px" flexDirection="column">
        <Spinner size="xl" />
        <Text mt={4}>Loading 3D Visualization for net: <Text as="span" fontWeight="bold">{selectedNet}</Text>...</Text>
      </Center>
    );
  }

  if (error) {
    return (
      <Center minH="500px" flexDirection="column" p={4} borderWidth="1px" borderRadius="md" borderColor="red.300" bg="red.50">
        <Heading size="md" color="red.600" mb={2}>Could not load 3D Visualization</Heading>
        <Text color="red.700">Error: {error}</Text>
        <Text color="gray.600" mt={2} fontSize="sm">Please ensure the backend is running and the selected net exists.</Text>
      </Center>
    );
  }

  if (!figureSpec || !figureSpec.data || !figureSpec.layout) {
    return (
      <Center minH="500px">
        <Text>No 3D visualization data available for net: <Text as="span" fontWeight="bold">{selectedNet}</Text>.</Text>
      </Center>
    );
  }

  return (
    <Box width="100%" height="650px"> {/* Ensure Box has dimensions for Plotly to render into */}
      <Plot
        data={figureSpec.data}
        layout={{
          ...figureSpec.layout,
          height: 650, // Explicitly set height for the plot layout
          // title: `3D Visualization: Net ${selectedNet}`, // Override title if needed or ensure backend provides good one
          margin: { l: 0, r: 0, b: 0, t: figureSpec.layout.title ? 40 : 0 } // Adjust top margin based on title presence
        }}
        style={{ width: '100%', height: '100%' }}
        config={{
          responsive: true, // Makes the plot responsive to container size changes
          displaylogo: false, // Hide Plotly logo
          // Add other Plotly config options here if needed
        }}
      />
    </Box>
  );
};

export default NetVisualization3D; 