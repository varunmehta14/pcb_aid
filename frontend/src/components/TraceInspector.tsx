import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  VStack,
  HStack,
  Spinner,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Switch,
  Flex
} from '@chakra-ui/react'
import { getTracePath, calculateTrace, getNetComponents, TraceResponse, Component } from '../api/boardApi'

interface TraceInspectorProps {
  boardId: string
  selectedNet: string
}

const TraceInspector: React.FC<TraceInspectorProps> = ({ boardId, selectedNet }) => {
  const [loading, setLoading] = useState(false)
  const [components, setComponents] = useState<Component[]>([])
  const [startComponent, setStartComponent] = useState<string>('')
  const [startPad, setStartPad] = useState<string>('')
  const [endComponent, setEndComponent] = useState<string>('')
  const [endPad, setEndPad] = useState<string>('')
  const [traceResult, setTraceResult] = useState<TraceResponse | null>(null)
  const [availableStartPads, setAvailableStartPads] = useState<string[]>([])
  const [availableEndPads, setAvailableEndPads] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showDetailedPath, setShowDetailedPath] = useState(true)
  const toast = useToast()

  // Reset state when selected net changes
  useEffect(() => {
    // Clear previous results when net changes
    setTraceResult(null);
    setStartComponent('');
    setStartPad('');
    setEndComponent('');
    setEndPad('');
    setError(null);
  }, [selectedNet]);

  // Fetch components and pads for the selected net
  useEffect(() => {
    if (!boardId || !selectedNet) return

    const fetchNetComponents = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Use the API to fetch components for the selected net
        const netComponents = await getNetComponents(boardId, selectedNet)
        setComponents(netComponents)
        
        // Set default selections if available
        if (netComponents.length > 0) {
          setStartComponent(netComponents[0].designator)
          if (netComponents[0].pads.length > 0) {
            setStartPad(netComponents[0].pads[0].padNumber)
          }
          
          if (netComponents.length > 1) {
            setEndComponent(netComponents[1].designator)
            if (netComponents[1].pads.length > 0) {
              setEndPad(netComponents[1].pads[0].padNumber)
            }
          }
        }
        
        setLoading(false)
      } catch (err) {
        console.error('Error fetching components for net:', err)
        toast({
          title: 'Error',
          description: `Failed to load components for net: ${selectedNet}`,
          status: 'error',
          duration: 5000,
          isClosable: true
        })
        setLoading(false)
      }
    }
    
    fetchNetComponents()
  }, [boardId, selectedNet, toast])
  
  // Update available pads when components change
  useEffect(() => {
    // Update start pads
    const startComp = components.find(c => c.designator === startComponent)
    if (startComp) {
      const pads = startComp.pads.map(p => p.padNumber)
      setAvailableStartPads(pads)
      
      // Reset pad selection if current selection is not valid
      if (pads.length > 0 && !pads.includes(startPad)) {
        setStartPad(pads[0])
      }
    } else {
      setAvailableStartPads([])
    }
    
    // Update end pads
    const endComp = components.find(c => c.designator === endComponent)
    if (endComp) {
      const pads = endComp.pads.map(p => p.padNumber)
      setAvailableEndPads(pads)
      
      // Reset pad selection if current selection is not valid
      if (pads.length > 0 && !pads.includes(endPad)) {
        setEndPad(pads[0])
      }
    } else {
      setAvailableEndPads([])
    }
  }, [components, startComponent, endComponent, startPad, endPad])
  
  const handleCalculateTrace = async () => {
    if (!startComponent || !startPad || !endComponent || !endPad) {
      toast({
        title: 'Error',
        description: 'Please select both start and end pads',
        status: 'error',
        duration: 3000,
        isClosable: true
      })
      return
    }
    
    try {
      setLoading(true)
      setError(null)
      setTraceResult(null)
      
      // Prepare request data
      const requestData = {
        net_name: selectedNet,
        start_component: startComponent,
        start_pad: startPad,
        end_component: endComponent,
        end_pad: endPad
      }
      
      // Use either detailed path or basic trace calculation based on toggle
      const result = showDetailedPath 
        ? await getTracePath(boardId, requestData)
        : await calculateTrace(boardId, requestData)
      
      setTraceResult(result)
      setLoading(false)
    } catch (err: any) {
      console.error('Error calculating trace:', err)
      
      // Extract error message from the response if available
      const errorMessage = err.response?.data?.detail || 
                          'Failed to calculate trace. The connection might not exist.';
      
      setError(errorMessage)
      toast({
        title: 'Error',
        description: `Failed to calculate trace for ${selectedNet}. ${errorMessage}`,
        status: 'error',
        duration: 5000,
        isClosable: true
      })
      setTraceResult(null)
      setLoading(false)
    }
  }
  
  const renderTraceDetails = () => {
    if (!traceResult) return null
    
    return (
      <Box mt={6} p={4} borderWidth="1px" borderRadius="md" bg="white">
        <Heading size="sm" mb={4}>Trace Details for {selectedNet}</Heading>
        
        <VStack align="stretch" spacing={4}>
          <HStack>
            <Text fontWeight="bold" width="150px">From:</Text>
            <Text>{traceResult.start_component}.{traceResult.start_pad}</Text>
          </HStack>
          
          <HStack>
            <Text fontWeight="bold" width="150px">To:</Text>
            <Text>{traceResult.end_component}.{traceResult.end_pad}</Text>
          </HStack>
          
          <HStack>
            <Text fontWeight="bold" width="150px">Net:</Text>
            <Text>{traceResult.net_name}</Text>
          </HStack>
          
          <HStack>
            <Text fontWeight="bold" width="150px">Length:</Text>
            <Text>{traceResult.length_mm?.toFixed(3)} mm</Text>
          </HStack>
          
          {showDetailedPath && traceResult.path_elements && (
            <Box>
              <Text fontWeight="bold" mb={2}>Path Elements:</Text>
              
              <Box maxHeight="250px" overflowY="auto">
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Type</Th>
                      <Th>Details</Th>
                      <Th>Layer</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {traceResult.path_elements?.map((element, index) => (
                      <Tr key={index}>
                        <Td>{element.type}</Td>
                        <Td>
                          {element.type === 'Pad' && `${element.component}.${element.pad}`}
                          {element.type === 'Track' && `Track (${element.length?.toFixed(2)} mils)`}
                          {element.type === 'Arc' && `Arc R=${element.radius?.toFixed(2)}`}
                          {element.type === 'Via' && `Via`}
                        </Td>
                        <Td>{element.layer}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            </Box>
          )}
          
          {showDetailedPath && traceResult.path_description && (
            <HStack>
              <Text fontWeight="bold" width="150px">Path:</Text>
              <Text>{traceResult.path_description}</Text>
            </HStack>
          )}
        </VStack>
      </Box>
    )
  }
  
  // Show a message when no components are found for the selected net
  const renderNoComponentsMessage = () => {
    if (!loading && components.length === 0) {
      return (
        <Box mb={6} p={4} borderWidth="1px" borderRadius="md" bg="white">
          <Text>No components found for net: {selectedNet}</Text>
        </Box>
      )
    }
    return null;
  }
  
  // Show error message if trace calculation failed
  const renderErrorMessage = () => {
    if (error) {
      return (
        <Alert status="error" mt={6} borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Unable to calculate trace path</AlertTitle>
            <AlertDescription>
              {error}
              <Text mt={2} fontSize="sm">
                Try a different component/pad combination or check if this connection exists.
              </Text>
            </AlertDescription>
          </Box>
        </Alert>
      )
    }
    return null;
  }
  
  return (
    <Box>
      <Box mb={6} p={4} borderWidth="1px" borderRadius="md" bg="white">
        <Heading size="sm" mb={4}>Trace Inspector for {selectedNet}</Heading>
        
        {renderNoComponentsMessage()}
        
        {components.length > 0 && (
          <VStack spacing={4} align="stretch">
            <HStack spacing={4}>
              <FormControl>
                <FormLabel>Start Component</FormLabel>
                <Select
                  value={startComponent}
                  onChange={(e) => setStartComponent(e.target.value)}
                  isDisabled={loading}
                >
                  {components.map(comp => (
                    <option key={`start-${comp.designator}`} value={comp.designator}>
                      {comp.designator}
                    </option>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel>Start Pad</FormLabel>
                <Select
                  value={startPad}
                  onChange={(e) => setStartPad(e.target.value)}
                  isDisabled={loading || availableStartPads.length === 0}
                >
                  {availableStartPads.map(pad => (
                    <option key={`start-pad-${pad}`} value={pad}>
                      {pad}
                    </option>
                  ))}
                </Select>
              </FormControl>
            </HStack>
            
            <HStack spacing={4}>
              <FormControl>
                <FormLabel>End Component</FormLabel>
                <Select
                  value={endComponent}
                  onChange={(e) => setEndComponent(e.target.value)}
                  isDisabled={loading}
                >
                  {components.map(comp => (
                    <option key={`end-${comp.designator}`} value={comp.designator}>
                      {comp.designator}
                    </option>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel>End Pad</FormLabel>
                <Select
                  value={endPad}
                  onChange={(e) => setEndPad(e.target.value)}
                  isDisabled={loading || availableEndPads.length === 0}
                >
                  {availableEndPads.map(pad => (
                    <option key={`end-pad-${pad}`} value={pad}>
                      {pad}
                    </option>
                  ))}
                </Select>
              </FormControl>
            </HStack>
            
            <Flex align="center" mb={2}>
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="detailed-path" mb="0">
                  Show detailed path
                </FormLabel>
                <Switch 
                  id="detailed-path" 
                  isChecked={showDetailedPath}
                  onChange={(e) => setShowDetailedPath(e.target.checked)}
                  colorScheme="blue"
                />
              </FormControl>
            </Flex>
            
            <Box>
              <Button
                colorScheme="blue"
                onClick={handleCalculateTrace}
                isLoading={loading}
                isDisabled={!startComponent || !startPad || !endComponent || !endPad}
              >
                {showDetailedPath ? 'Show Trace Path' : 'Calculate Trace Length'}
              </Button>
            </Box>
          </VStack>
        )}
      </Box>
      
      {loading ? (
        <Box display="flex" justifyContent="center" py={10}>
          <Spinner size="xl" />
        </Box>
      ) : (
        <>
          {renderErrorMessage()}
          {renderTraceDetails()}
        </>
      )}
    </Box>
  )
}

export default TraceInspector 