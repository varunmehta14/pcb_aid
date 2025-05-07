import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Text,
  useToast,
  VStack,
  Image,
} from '@chakra-ui/react'
import FileUpload from '../components/FileUpload'
import { uploadPCBFile } from '../api/boardApi'

const UploadPage = () => {
  const [isUploading, setIsUploading] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  const handleFileUpload = async (file: File) => {
    if (!file) return

    setIsUploading(true)
    try {
      const response = await uploadPCBFile(file)
      toast({
        title: 'Upload successful',
        description: `File ${file.name} has been processed successfully.`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      // Navigate to dashboard with the new board ID
      navigate(`/dashboard/${response.session_id}`)
    } catch (error) {
      console.error('Upload error:', error)
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Container maxW="container.xl" py={10}>
      <VStack spacing={8} align="center">
        <Heading as="h1" size="xl">
          PCB AiD - Analyzer & Intelligent Design Assistant
        </Heading>
        
        <Text fontSize="lg" textAlign="center" maxW="container.md">
          Upload your PCB JSON file to analyze trace lengths, visualize nets, and get AI-powered insights.
        </Text>

        <Box
          w="full"
          p={10}
          borderWidth="1px"
          borderRadius="lg"
          bg="white"
          boxShadow="lg"
        >
          <VStack spacing={6}>
            <Heading as="h2" size="md">
              Upload PCB File
            </Heading>
            
            <FileUpload
              accept=".json"
              multiple={false}
              isUploading={isUploading}
              onFileUpload={handleFileUpload}
            />
            
            <Text fontSize="sm" color="gray.500">
              Supported format: JSON exports from PCB design tools
            </Text>
          </VStack>
        </Box>
      </VStack>
    </Container>
  )
}

export default UploadPage 