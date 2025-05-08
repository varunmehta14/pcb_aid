import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Flex,
  Spinner,
  Progress,
  Badge,
  VStack,
  useToast,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid
} from '@chakra-ui/react'
import { getTracePath, TraceResponse, getCriticalPaths, PathInfo } from '../api/boardApi'

interface CriticalPathAnalysisProps {
  boardId: string
  selectedNet: string
}

const CriticalPathAnalysis: React.FC<CriticalPathAnalysisProps> = ({ boardId, selectedNet }) => {
  const [loading, setLoading] = useState(true)
  const [criticalPaths, setCriticalPaths] = useState<PathInfo[]>([])
  const [totalLength, setTotalLength] = useState(0)
  const [maxLength, setMaxLength] = useState(0)
  const [selectedPath, setSelectedPath] = useState<TraceResponse | null>(null)
  const [analyzingPath, setAnalyzingPath] = useState(false)
  const toast = useToast()

  // Fetch critical paths for the selected net
  useEffect(() => {
    if (!boardId || !selectedNet) return

    const fetchCriticalPaths = async () => {
      try {
        setLoading(true)
        
        // Use our new API endpoint to get critical paths
        const pathsData = await getCriticalPaths(boardId, selectedNet)
        
        // Sort by length (descending)
        const sortedPaths = [...pathsData.paths].sort((a, b) => b.length_mm - a.length_mm)
        
        setCriticalPaths(sortedPaths)
        
        // Set statistics
        if (sortedPaths.length > 0) {
          setMaxLength(sortedPaths[0].length_mm)
          setTotalLength(pathsData.total_length_mm)
        }
        
        setLoading(false)
      } catch (err) {
        console.error('Error analyzing critical paths:', err)
        toast({
          title: 'Error',
          description: 'Failed to analyze critical paths for the selected net',
          status: 'error',
          duration: 5000,
          isClosable: true
        })
        setLoading(false)
      }
    }
    
    fetchCriticalPaths()
  }, [boardId, selectedNet, toast])
  
  const handleViewPathDetails = async (path: PathInfo) => {
    try {
      setAnalyzingPath(true)
      
      const result = await getTracePath(boardId, {
        net_name: selectedNet,
        start_component: path.start_component,
        start_pad: path.start_pad,
        end_component: path.end_component,
        end_pad: path.end_pad
      })
      
      setSelectedPath(result)
      setAnalyzingPath(false)
    } catch (err) {
      console.error('Error fetching path details:', err)
      toast({
        title: 'Error',
        description: 'Failed to retrieve path details',
        status: 'error',
        duration: 5000,
        isClosable: true
      })
      setAnalyzingPath(false)
    }
  }
  
  const renderPathDetails = () => {
    if (!selectedPath) return null
    
    return (
      <Box mt={6} p={4} borderWidth="1px" borderRadius="md" bg="white">
        <Heading size="sm" mb={4}>Path Details</Heading>
        
        <SimpleGrid columns={2} spacing={4} mb={4}>
          <Box>
            <Stat>
              <StatLabel>Path Length</StatLabel>
              <StatNumber>{selectedPath.length_mm?.toFixed(3)} mm</StatNumber>
              <StatHelpText>
                {((selectedPath.length_mm || 0) / maxLength * 100).toFixed(1)}% of max length
              </StatHelpText>
            </Stat>
          </Box>
          
          <Box>
            <Stat>
              <StatLabel>Connection</StatLabel>
              <StatNumber>
                {selectedPath.path_elements?.length || 0} elements
              </StatNumber>
              <StatHelpText>
                {selectedPath.start_component}.{selectedPath.start_pad} to {selectedPath.end_component}.{selectedPath.end_pad}
              </StatHelpText>
            </Stat>
          </Box>
        </SimpleGrid>
        
        <Box maxHeight="250px" overflowY="auto">
          <Table size="sm" variant="simple">
            <Thead>
              <Tr>
                <Th>Type</Th>
                <Th>Details</Th>
                <Th>Layer</Th>
                <Th>Length</Th>
              </Tr>
            </Thead>
            <Tbody>
              {selectedPath.path_elements?.map((element, index) => (
                <Tr key={index}>
                  <Td>{element.type}</Td>
                  <Td>
                    {element.type === 'Pad' && `${element.component}.${element.pad}`}
                    {element.type === 'Track' && `Track`}
                    {element.type === 'Arc' && element.radius ? `Arc R=${element.radius.toFixed(2)}` : 'Arc'}
                    {element.type === 'Via' && `Via`}
                  </Td>
                  <Td>{element.layer}</Td>
                  <Td>
                    {(element.type === 'Track' || element.type === 'Arc') && element.length 
                      ? `${element.length.toFixed(3)} mils` 
                      : '-'}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      </Box>
    )
  }
  
  const renderPathAnalysis = () => {
    return (
      <Box mt={6} p={4} borderWidth="1px" borderRadius="md" bg="white">
        <Heading size="sm" mb={4}>Critical Paths Analysis</Heading>
        
        <SimpleGrid columns={2} spacing={4} mb={4}>
          <Box>
            <Stat>
              <StatLabel>Maximum Path Length</StatLabel>
              <StatNumber>{maxLength.toFixed(3)} mm</StatNumber>
              <StatHelpText>
                Longest trace in the net
              </StatHelpText>
            </Stat>
          </Box>
          
          <Box>
            <Stat>
              <StatLabel>Total Trace Length</StatLabel>
              <StatNumber>{totalLength.toFixed(3)} mm</StatNumber>
              <StatHelpText>
                Combined length of all critical paths
              </StatHelpText>
            </Stat>
          </Box>
        </SimpleGrid>
        
        <Table variant="simple" size="sm">
          <Thead>
            <Tr>
              <Th>Rank</Th>
              <Th>From</Th>
              <Th>To</Th>
              <Th>Length (mm)</Th>
              <Th>% of Max</Th>
              <Th>Action</Th>
            </Tr>
          </Thead>
          <Tbody>
            {criticalPaths.map((path, index) => (
              <Tr key={index}>
                <Td>{index + 1}</Td>
                <Td>{path.start_component}.{path.start_pad}</Td>
                <Td>{path.end_component}.{path.end_pad}</Td>
                <Td>{path.length_mm.toFixed(3)}</Td>
                <Td>
                  <Flex align="center">
                    <Text width="40px" mr={2}>
                      {((path.length_mm / maxLength) * 100).toFixed(0)}%
                    </Text>
                    <Progress
                      flex="1"
                      value={(path.length_mm / maxLength) * 100}
                      colorScheme={index === 0 ? "red" : index < 3 ? "orange" : "green"}
                      size="sm"
                    />
                  </Flex>
                </Td>
                <Td>
                  <Button
                    size="xs"
                    colorScheme="blue"
                    onClick={() => handleViewPathDetails(path)}
                    isLoading={analyzingPath}
                  >
                    View
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    )
  }
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <VStack>
          <Spinner size="xl" mb={4} />
          <Text>Analyzing critical paths...</Text>
        </VStack>
      </Box>
    )
  }
  
  if (criticalPaths.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <Text>No critical paths found for the selected net</Text>
      </Box>
    )
  }
  
  return (
    <Box>
      <Heading size="md" mb={4}>
        Critical Path Analysis for{' '}
        <Badge colorScheme="blue" fontSize="md">{selectedNet}</Badge>
      </Heading>
      
      {renderPathAnalysis()}
      
      {analyzingPath ? (
        <Box display="flex" justifyContent="center" py={10}>
          <Spinner size="xl" />
        </Box>
      ) : renderPathDetails()}
    </Box>
  )
}

export default CriticalPathAnalysis 