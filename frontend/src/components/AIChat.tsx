import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Container,
  Flex,
  Input,
  Text,
  VStack,
  useToast,
  Badge,
  Spinner,
} from '@chakra-ui/react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  taskId?: string
}

interface AIChatProps {
  boardId: string
}

interface TaskStatus {
  task_id: string
  status: string
  elapsed_time: number
  result?: string
  error?: string
}

const AIChat = ({ boardId }: AIChatProps) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeTasks, setActiveTasks] = useState<string[]>([])
  const pollingIntervalRef = useRef<number | null>(null)
  const toast = useToast()

  // Clean up intervals when component unmounts
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        window.clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  // Start polling for task status updates
  const startPolling = () => {
    if (pollingIntervalRef.current) {
      window.clearInterval(pollingIntervalRef.current)
    }

    pollingIntervalRef.current = window.setInterval(() => {
      if (activeTasks.length === 0) {
        if (pollingIntervalRef.current) {
          window.clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
        return
      }

      // Poll for status updates on all active tasks
      activeTasks.forEach(checkTaskStatus)
    }, 2000) // Poll every 2 seconds
  }

  // Check status of a specific task
  const checkTaskStatus = async (taskId: string) => {
    try {
      const response = await axios.get(`/api/board/analyze/task/${taskId}`)
      const taskStatus: TaskStatus = response.data

      if (taskStatus.status === 'completed' && taskStatus.result) {
        // Task completed successfully - update the message
        updateTaskMessage(taskId, 'assistant', taskStatus.result)
        
        // Remove from active tasks
        setActiveTasks(prev => prev.filter(id => id !== taskId))
      } 
      else if (taskStatus.status === 'error' && taskStatus.error) {
        // Task failed - update with error message
        updateTaskMessage(taskId, 'system', `Error: ${taskStatus.error}`)
        
        // Remove from active tasks
        setActiveTasks(prev => prev.filter(id => id !== taskId))
      }
      else if (taskStatus.status === 'cancelled') {
        // Task was cancelled
        updateTaskMessage(taskId, 'system', 'Analysis was cancelled')
        
        // Remove from active tasks
        setActiveTasks(prev => prev.filter(id => id !== taskId))
      }
      else if (taskStatus.elapsed_time > 60) {
        // Task is taking too long - offer to cancel
        updateTaskMessage(
          taskId, 
          'system',
          `Analysis is taking longer than expected (${Math.round(taskStatus.elapsed_time)}s). You can cancel it and try a more specific query.`,
          false // Don't replace existing message, just update it
        )
      }
    } catch (error) {
      console.error(`Error checking task ${taskId} status:`, error)
    }
  }

  // Update a message for a specific task
  const updateTaskMessage = (taskId: string, role: 'assistant' | 'system', content: string, replace = true) => {
    setMessages(prev => {
      const newMessages = [...prev]
      const taskMsgIndex = newMessages.findIndex(msg => msg.taskId === taskId)
      
      if (taskMsgIndex >= 0) {
        if (replace) {
          // Replace the entire message
          newMessages[taskMsgIndex] = { role, content, taskId }
        } else {
          // Just update the content while keeping the same role
          newMessages[taskMsgIndex] = { 
            ...newMessages[taskMsgIndex],
            content 
          }
        }
      }
      
      return newMessages
    })
  }

  // Cancel an active task
  const cancelTask = async (taskId: string) => {
    try {
      await axios.delete(`/api/board/analyze/task/${taskId}`)
      toast({
        title: 'Task cancelled',
        description: 'The analysis task has been cancelled',
        status: 'info',
        duration: 3000,
        isClosable: true,
      })
      
      // Update the message directly
      updateTaskMessage(taskId, 'system', 'Analysis was cancelled by user')
      
      // Remove from active tasks
      setActiveTasks(prev => prev.filter(id => id !== taskId))
    } catch (error) {
      console.error(`Error cancelling task ${taskId}:`, error)
      toast({
        title: 'Error',
        description: 'Failed to cancel the task',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    // Add user message
    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Check if this is a complex query that might need async processing
      const isComplexQuery = 
        input.length > 100 || 
        input.includes('designator') || 
        input.includes('analyze the trace') ||
        input.includes('redesign') ||
        input.includes('all possible ways');
      
      if (isComplexQuery) {
        // Use the async endpoint for complex queries
        const response = await axios.post(`/api/board/${boardId}/analyze/async`, {
          query: input,
        })
        
        // Add a placeholder message that will be updated later
        const taskId = response.data.task_id
        const placeholderMsg: Message = { 
          role: 'assistant', 
          content: 'Analyzing PCB data... this may take a moment.', 
          taskId 
        }
        
        setMessages(prev => [...prev, placeholderMsg])
        
        // Add to active tasks and start polling
        setActiveTasks(prev => [...prev, taskId])
        startPolling()
      } else {
        // Use the regular endpoint for simple queries
        const response = await axios.post(`/api/board/${boardId}/analyze`, {
          query: input,
        })

        // Add AI response
        const aiMessage: Message = {
          role: 'assistant',
          content: response.data.result || response.data.response || 'No response received',
        }
        setMessages(prev => [...prev, aiMessage])
      }
    } catch (error) {
      console.error('Error getting AI response:', error)
      toast({
        title: 'Error',
        description: 'Failed to get AI analysis',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      
      // Add error message
      const errorMessage: Message = {
        role: 'system',
        content: 'Failed to analyze PCB. Please try a more specific query or check your connection.',
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        {/* Messages */}
        <Box
          flex="1"
          overflowY="auto"
          p={4}
          borderWidth="1px"
          borderRadius="md"
          minH="400px"
          maxH="600px"
        >
          {messages.map((message, index) => (
            <Box
              key={index}
              mb={4}
              p={3}
              borderRadius="md"
              bg={
                message.role === 'user' 
                  ? 'blue.50' 
                  : message.role === 'system' 
                    ? 'red.50' 
                    : 'gray.50'
              }
            >
              <Flex justify="space-between" align="center" mb={1}>
                <Text fontWeight="bold">
                  {message.role === 'user' 
                    ? 'You' 
                    : message.role === 'system' 
                      ? 'System' 
                      : 'PCB AiD'}
                </Text>
                
                {/* Show cancel button for active tasks */}
                {message.taskId && activeTasks.includes(message.taskId) && (
                  <Flex align="center">
                    <Spinner size="xs" mr={2} />
                    <Badge colorScheme="blue" mr={2}>Processing</Badge>
                    <Button 
                      size="xs" 
                      colorScheme="red" 
                      onClick={() => cancelTask(message.taskId!)}
                    >
                      Cancel
                    </Button>
                  </Flex>
                )}
              </Flex>
              <Text whiteSpace="pre-wrap">{message.content}</Text>
            </Box>
          ))}
        </Box>

        {/* Input form */}
        <form onSubmit={handleSubmit}>
          <Flex>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your PCB design..."
              mr={2}
              disabled={isLoading}
            />
            <Button
              type="submit"
              colorScheme="blue"
              isLoading={isLoading}
              loadingText="Analyzing..."
            >
              Send
            </Button>
          </Flex>
        </form>
      </VStack>
    </Container>
  )
}

export default AIChat 