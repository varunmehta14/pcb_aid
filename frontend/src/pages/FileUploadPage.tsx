import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Container,
  Heading,
  Text,
  useToast,
  VStack,
} from '@chakra-ui/react'
import { uploadPCBFile } from '../api/boardApi'

const FileUploadPage = () => {
  const [isUploading, setIsUploading] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setIsUploading(true)
      const response = await uploadPCBFile(file)
      toast({
        title: 'Success',
        description: 'PCB file uploaded successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
      navigate(`/board/${response.session_id}`)
    } catch (error) {
      console.error('Error uploading file:', error)
      toast({
        title: 'Error',
        description: 'Failed to upload PCB file',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Container maxW="container.md" py={10}>
      <VStack spacing={8}>
        <Heading as="h1" size="xl">
          PCB AiD - File Upload
        </Heading>
        
        <Box
          p={10}
          borderWidth="2px"
          borderRadius="lg"
          borderStyle="dashed"
          textAlign="center"
          width="100%"
        >
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            id="file-upload"
            disabled={isUploading}
          />
          <label htmlFor="file-upload">
            <Button
              as="span"
              colorScheme="blue"
              size="lg"
              isLoading={isUploading}
              loadingText="Uploading..."
              cursor="pointer"
            >
              Select PCB File
            </Button>
          </label>
          <Text mt={4} color="gray.600">
            Upload your PCB JSON file to begin analysis
          </Text>
        </Box>
      </VStack>
    </Container>
  )
}

export default FileUploadPage 