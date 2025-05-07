import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box,
  Container,
  Flex,
  Grid,
  GridItem,
  Heading,
  Select,
  Spinner,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  useToast,
} from '@chakra-ui/react'
import { getNetList, NetInfo } from '../api/boardApi'
import AIChat from '../components/AIChat'
import PCBVisualizer from '../components/PCBVisualizer'
import TraceInspector from '../components/TraceInspector'
import CriticalPathAnalysis from '../components/CriticalPathAnalysis'

const DashboardPage = () => {
  const { boardId } = useParams<{ boardId: string }>()
  const [isLoading, setIsLoading] = useState(true)
  const [nets, setNets] = useState<NetInfo[]>([])
  const [selectedNet, setSelectedNet] = useState<string>('')
  const toast = useToast()

  useEffect(() => {
    const fetchNetList = async () => {
      if (!boardId) return
      
      try {
        setIsLoading(true)
        const netList = await getNetList(boardId)
        setNets(netList)
        
        // Select the first net by default if available
        if (netList.length > 0) {
          setSelectedNet(netList[0].net_name)
        }
      } catch (error) {
        console.error('Error fetching net list:', error)
        toast({
          title: 'Error',
          description: 'Failed to load PCB net list.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchNetList()
  }, [boardId, toast])

  const handleNetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedNet(e.target.value)
  }

  return (
    <Container maxW="container.xl" py={6}>
      <Heading as="h1" size="xl" mb={6}>
        PCB Analysis Dashboard
      </Heading>

      {isLoading ? (
        <Flex justify="center" align="center" minH="60vh">
          <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
        </Flex>
      ) : (
        <Grid templateColumns="repeat(12, 1fr)" gap={6}>
          {/* Sidebar */}
          <GridItem colSpan={{ base: 12, md: 3 }}>
            <Box p={4} borderWidth="1px" borderRadius="md" bg="white">
              <Heading as="h3" size="md" mb={4}>
                Net Selection
              </Heading>
              
              <Select
                value={selectedNet}
                onChange={handleNetChange}
                placeholder="Select a net"
                mb={4}
              >
                {nets.map((net) => (
                  <option key={net.net_name} value={net.net_name}>
                    {net.net_name} ({net.component_count} comp., {net.pad_count} pads)
                  </option>
                ))}
              </Select>
              
              <Text fontSize="sm" color="gray.600">
                {selectedNet ? (
                  <>
                    Selected: <Text as="span" fontWeight="bold">{selectedNet}</Text>
                  </>
                ) : (
                  'Please select a net to analyze'
                )}
              </Text>
            </Box>
          </GridItem>

          {/* Main Content */}
          <GridItem colSpan={{ base: 12, md: 9 }}>
            <Box borderWidth="1px" borderRadius="md" bg="white">
              <Tabs isLazy>
                <TabList>
                  <Tab>Visualization</Tab>
                  <Tab>Trace Inspector</Tab>
                  <Tab>Critical Path Analysis</Tab>
                  <Tab>AI Assistant</Tab>
                </TabList>

                <TabPanels>
                  {/* Visualization Tab */}
                  <TabPanel>
                    <Box minH="500px">
                      {boardId && selectedNet ? (
                        <PCBVisualizer 
                          boardId={boardId} 
                          selectedNet={selectedNet}
                        />
                      ) : (
                        <Text>Please select a board and net to visualize</Text>
                      )}
                    </Box>
                  </TabPanel>

                  {/* Trace Inspector Tab */}
                  <TabPanel>
                    <Box minH="500px">
                      {boardId && selectedNet ? (
                        <TraceInspector
                          boardId={boardId}
                          selectedNet={selectedNet}
                        />
                      ) : (
                        <Text>Please select a board and net to inspect traces</Text>
                      )}
                    </Box>
                  </TabPanel>

                  {/* Critical Path Analysis Tab */}
                  <TabPanel>
                    <Box minH="500px">
                      {boardId && selectedNet ? (
                        <CriticalPathAnalysis
                          boardId={boardId}
                          selectedNet={selectedNet}
                        />
                      ) : (
                        <Text>Please select a board and net for critical path analysis</Text>
                      )}
                    </Box>
                  </TabPanel>

                  {/* AI Assistant Tab */}
                  <TabPanel>
                    {boardId && <AIChat boardId={boardId} />}
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </Box>
          </GridItem>
        </Grid>
      )}
    </Container>
  )
}

export default DashboardPage 