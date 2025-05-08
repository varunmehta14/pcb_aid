import { useEffect, useState, useRef } from 'react'
import { Box, Spinner, Text } from '@chakra-ui/react'
import { Stage, Layer, Line, Circle, Text as KonvaText } from 'react-konva'
import { getNetVisualization } from '../api/boardApi'

interface PCBVisualizerProps {
  boardId: string
  selectedNet: string
}

// Constants for visualization
const PADDING = 50
const SCALE_FACTOR = 0.5
const PAD_RADIUS = 2
const TRACK_WIDTH = 1
const COLORS = {
  pad: '#e74c3c',
  track: '#3498db',
  via: '#2ecc71',
  arc: '#9b59b6',
  selected: '#f39c12',
  background: '#f5f5f5',
  text: '#2c3e50'
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
  
  const renderPad = (element: any, index: number) => {
    const point = transformPoint(element.location)
    
    return (
      <>
        <Circle
          key={`pad-${index}`}
          x={point.x}
          y={point.y}
          radius={PAD_RADIUS * 3}
          fill={COLORS.pad}
        />
        <KonvaText
          key={`pad-text-${index}`}
          x={point.x + PAD_RADIUS * 4}
          y={point.y - PAD_RADIUS * 4}
          text={`${element.component}.${element.pad}`}
          fontSize={10}
          fill={COLORS.text}
        />
      </>
    )
  }
  
  const renderTrack = (element: any, index: number) => {
    const start = transformPoint(element.start)
    const end = transformPoint(element.end)
    
    return (
      <Line
        key={`track-${index}`}
        points={[start.x, start.y, end.x, end.y]}
        stroke={COLORS.track}
        strokeWidth={TRACK_WIDTH}
      />
    )
  }
  
  const renderArc = (element: any, index: number) => {
    // For simplicity, we'll approximate the arc with a series of line segments
    const center = transformPoint(element.center)
    const radius = element.radius * SCALE_FACTOR
    const startAngle = element.start_angle * Math.PI / 180
    const endAngle = element.end_angle * Math.PI / 180
    
    // Generate points along the arc
    const numSegments = 32
    const points: number[] = []
    
    for (let i = 0; i <= numSegments; i++) {
      const angle = startAngle + (endAngle - startAngle) * (i / numSegments)
      const x = center.x + radius * Math.cos(angle)
      const y = center.y + radius * Math.sin(angle)
      points.push(x, y)
    }
    
    return (
      <Line
        key={`arc-${index}`}
        points={points}
        stroke={COLORS.arc}
        strokeWidth={TRACK_WIDTH}
      />
    )
  }
  
  const renderVia = (element: any, index: number) => {
    const point = transformPoint(element.location)
    
    return (
      <Circle
        key={`via-${index}`}
        x={point.x}
        y={point.y}
        radius={PAD_RADIUS * 2}
        fill={COLORS.via}
      />
    )
  }
  
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
      <Stage width={stageSize.width} height={stageSize.height} ref={stageRef}>
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