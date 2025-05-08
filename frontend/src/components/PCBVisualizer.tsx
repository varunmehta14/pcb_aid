import { useEffect, useState, useRef } from 'react'
import { Box, Spinner, Text } from '@chakra-ui/react'
import { Stage, Layer, Line, Circle, Text as KonvaText, Rect, Group } from 'react-konva'
import { getNetVisualization } from '../api/boardApi'

interface PCBVisualizerProps {
  boardId: string
  selectedNet: string
}

// Constants for visualization
const PADDING = 50
const SCALE_FACTOR = 0.5
const PAD_RADIUS = 2
const TRACK_WIDTH = 1.5  // Slightly thicker for better visibility
const COLORS = {
  pad: '#e74c3c',
  track: '#3498db',
  via: '#2ecc71',
  arc: '#9b59b6',
  selected: '#f39c12',
  background: '#f5f5f5',
  text: '#2c3e50',
  padStroke: '#c0392b',
  viaStroke: '#27ae60',
  componentBody: 'rgba(189, 195, 199, 0.7)',
  componentStroke: '#7f8c8d'
}

interface Point {
  x: number
  y: number
}

const PCBVisualizer: React.FC<PCBVisualizerProps> = ({ boardId, selectedNet }) => {
  const [loading, setLoading] = useState(true)
  const [netData, setNetData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 })
  const [viewport, setViewport] = useState({ minX: 0, minY: 0, maxX: 1000, maxY: 1000 })
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const stageRef = useRef<any>(null)

  useEffect(() => {
    if (!boardId || !selectedNet) return
    
    const fetchNetData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Use our new API endpoint to get net visualization data
        const visualizationData = await getNetVisualization(boardId, selectedNet)
        setNetData(visualizationData)
        
        // Calculate viewport based on the actual geometry
        calculateViewport(visualizationData)
        
        setLoading(false)
      } catch (err) {
        console.error('Error fetching net visualization data:', err)
        setError('Failed to load visualization data for the selected net')
        setLoading(false)
      }
    }
    
    fetchNetData()
  }, [boardId, selectedNet])
  
  const calculateViewport = (data: any) => {
    // Initialize min/max values
    let minX = Number.MAX_SAFE_INTEGER
    let minY = Number.MAX_SAFE_INTEGER
    let maxX = Number.MIN_SAFE_INTEGER
    let maxY = Number.MIN_SAFE_INTEGER
    
    if (data?.path_elements) {
      // Iterate through all elements to find bounds
      data.path_elements.forEach((element: any) => {
        if (element.type === 'Pad' || element.type === 'Via') {
          const x = element.location[0]
          const y = element.location[1]
          minX = Math.min(minX, x)
          minY = Math.min(minY, y)
          maxX = Math.max(maxX, x)
          maxY = Math.max(maxY, y)
        } else if (element.type === 'Track') {
          const startX = element.start[0]
          const startY = element.start[1]
          const endX = element.end[0]
          const endY = element.end[1]
          minX = Math.min(minX, startX, endX)
          minY = Math.min(minY, startY, endY)
          maxX = Math.max(maxX, startX, endX)
          maxY = Math.max(maxY, startY, endY)
        } else if (element.type === 'Arc') {
          const startX = element.start[0]
          const startY = element.start[1]
          const endX = element.end[0]
          const endY = element.end[1]
          const centerX = element.center[0]
          const centerY = element.center[1]
          const radius = element.radius
          minX = Math.min(minX, centerX - radius, startX, endX)
          minY = Math.min(minY, centerY - radius, startY, endY)
          maxX = Math.max(maxX, centerX + radius, startX, endX)
          maxY = Math.max(maxY, centerY + radius, startY, endY)
        }
      })
      
      // Add padding
      const width = maxX - minX + 2 * PADDING
      const height = maxY - minY + 2 * PADDING
      
      // Update viewport bounds with padding
      minX -= PADDING
      minY -= PADDING
      maxX += PADDING
      maxY += PADDING
      
      setViewport({ minX, minY, maxX, maxY })
      
      // Set stage size based on viewport aspect ratio
      const containerWidth = 800
      const containerHeight = 600
      
      if (width / height > containerWidth / containerHeight) {
        // Width constrained
        const newHeight = (containerWidth / width) * height
        setStageSize({ width: containerWidth, height: newHeight })
      } else {
        // Height constrained
        const newWidth = (containerHeight / height) * width
        setStageSize({ width: newWidth, height: containerHeight })
      }
    }
  }
  
  const transformPoint = (point: [number, number]): Point => {
    const [x, y] = point
    const viewportWidth = viewport.maxX - viewport.minX
    const viewportHeight = viewport.maxY - viewport.minY
    
    return {
      x: ((x - viewport.minX) / viewportWidth) * stageSize.width,
      y: ((y - viewport.minY) / viewportHeight) * stageSize.height
    }
  }
  
  // Add wheel handler for zooming
  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    
    const stage = stageRef.current;
    const oldScale = scale;
    
    // Get pointer position relative to stage
    const pointer = stage.getPointerPosition();
    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale,
    };
    
    // Calculate new scale - limit min/max zoom
    const newScale = e.evt.deltaY < 0 ? oldScale * 1.1 : oldScale / 1.1;
    const limitedScale = Math.max(0.1, Math.min(10, newScale));
    
    // Update state
    setScale(limitedScale);
    
    // Calculate new position so we zoom into the mouse pointer
    const newPos = {
      x: pointer.x - mousePointTo.x * limitedScale,
      y: pointer.y - mousePointTo.y * limitedScale,
    };
    setPosition(newPos);
  };
  
  // Add drag handler for panning
  const handleDragStart = () => {
    // Optional: Add any logic needed on drag start
  };
  
  const handleDragEnd = (e: any) => {
    setPosition({ 
      x: e.target.x(),
      y: e.target.y()
    });
  };
  
  const renderPad = (element: any, index: number) => {
    const point = transformPoint(element.location);
    const isSquare = Math.random() > 0.5; // Randomly choose pad shape for variety (ideally this would be based on actual pad shape data)
    
    return (
      <Group key={`pad-group-${index}`}>
        {isSquare ? (
          <Rect
            x={point.x - PAD_RADIUS * 2.5}
            y={point.y - PAD_RADIUS * 2.5}
            width={PAD_RADIUS * 5}
            height={PAD_RADIUS * 5}
            fill={COLORS.pad}
            stroke={COLORS.padStroke}
            strokeWidth={0.5}
            cornerRadius={1}
          />
        ) : (
          <Circle
            x={point.x}
            y={point.y}
            radius={PAD_RADIUS * 3}
            fill={COLORS.pad}
            stroke={COLORS.padStroke}
            strokeWidth={0.5}
          />
        )}
        <KonvaText
          x={point.x + PAD_RADIUS * 4}
          y={point.y - PAD_RADIUS * 4}
          text={`${element.component}.${element.pad}`}
          fontSize={10}
          fill={COLORS.text}
        />
      </Group>
    );
  };
  
  const renderTrack = (element: any, index: number) => {
    const start = transformPoint(element.start);
    const end = transformPoint(element.end);
    
    return (
      <Line
        key={`track-${index}`}
        points={[start.x, start.y, end.x, end.y]}
        stroke={COLORS.track}
        strokeWidth={TRACK_WIDTH}
        lineCap="round"
        lineJoin="round"
      />
    );
  };
  
  const renderArc = (element: any, index: number) => {
    // Improved arc rendering with more segments for smoother curves
    const center = transformPoint(element.center);
    const start = transformPoint(element.start);
    const end = transformPoint(element.end);
    
    // Generate points along the arc
    const numSegments = 48; // Increased for smoother curves
    const points: number[] = [];
    
    // Use actual start and end points for more accuracy
    points.push(start.x, start.y);
    
    // Calculate angular distance
    let startAngle = element.start_angle;
    let endAngle = element.end_angle;
    
    // Handle angle wrapping
    if (endAngle < startAngle) {
      endAngle += 360;
    }
    
    // Convert to radians
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    
    // Generate intermediate points
    for (let i = 1; i < numSegments; i++) {
      const angle = startRad + ((endRad - startRad) * i) / numSegments;
      const radius = element.radius;
      const x = center.x + radius * Math.cos(angle) * (stageSize.width / (viewport.maxX - viewport.minX));
      const y = center.y + radius * Math.sin(angle) * (stageSize.height / (viewport.maxY - viewport.minY));
      points.push(x, y);
    }
    
    // Add the actual end point
    points.push(end.x, end.y);
    
    return (
      <Line
        key={`arc-${index}`}
        points={points}
        stroke={COLORS.arc}
        strokeWidth={TRACK_WIDTH}
        lineCap="round"
        lineJoin="round"
      />
    );
  };
  
  const renderVia = (element: any, index: number) => {
    const point = transformPoint(element.location);
    
    return (
      <Group key={`via-group-${index}`}>
        {/* Outer circle for via */}
        <Circle
          x={point.x}
          y={point.y}
          radius={PAD_RADIUS * 2.5}
          fill={COLORS.via}
          stroke={COLORS.viaStroke}
          strokeWidth={0.5}
        />
        {/* Inner circle for hole */}
        <Circle
          x={point.x}
          y={point.y}
          radius={PAD_RADIUS * 1.2}
          fill={COLORS.background}
        />
      </Group>
    );
  };
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <Spinner size="xl" />
      </Box>
    )
  }
  
  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <Text color="red.500">{error}</Text>
      </Box>
    )
  }
  
  if (!netData || !netData.path_elements || netData.path_elements.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <Text>No trace data available for the selected net</Text>
      </Box>
    )
  }
  
  return (
    <Box width="100%" height="400px" overflow="hidden" backgroundColor={COLORS.background}>
      <Stage 
        width={stageSize.width} 
        height={stageSize.height} 
        ref={stageRef}
        onWheel={handleWheel}
        draggable
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        x={position.x}
        y={position.y}
        scale={{ x: scale, y: scale }}
      >
        <Layer>
          {netData.path_elements.map((element: any, index: number) => {
            if (element.type === 'Pad') return renderPad(element, index)
            if (element.type === 'Track') return renderTrack(element, index)
            if (element.type === 'Arc') return renderArc(element, index)
            if (element.type === 'Via') return renderVia(element, index)
            return null
          })}
        </Layer>
      </Stage>
      
      <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
        {netData.start_component && netData.end_component ? (
          <>
            <Text fontSize="sm">
              Trace: {netData.start_component}.{netData.start_pad} to {netData.end_component}.{netData.end_pad}
            </Text>
            <Text fontSize="sm">
              Length: {netData.length_mm?.toFixed(2) || 'N/A'} mm
            </Text>
          </>
        ) : (
          <Text fontSize="sm">
            Net: {netData.net_name || selectedNet}
          </Text>
        )}
      </Box>
    </Box>
  )
}

export default PCBVisualizer 