import { useState } from 'react'
import {
  Box,
  Button,
  Container,
  Flex,
  Input,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface AIChatProps {
  boardId: string
}

const AIChat = ({ boardId }: AIChatProps) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const toast = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    // Add user message
    const userMessage: Message = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Send query to backend
      const response = await axios.post(`/api/board/${boardId}/analyze`, {
        query: input,
      })

      // Add AI response
      const aiMessage: Message = {
        role: 'assistant',
        content: response.data.response,
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error('Error getting AI response:', error)
      toast({
        title: 'Error',
        description: 'Failed to get AI analysis',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
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
              bg={message.role === 'user' ? 'blue.50' : 'gray.50'}
            >
              <Text fontWeight="bold" mb={1}>
                {message.role === 'user' ? 'You' : 'PCB AiD'}
              </Text>
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