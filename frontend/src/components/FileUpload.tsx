import { useRef, useState, ChangeEvent } from 'react'
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Icon,
  Input,
  Text,
  useColorModeValue,
  VStack,
} from '@chakra-ui/react'

interface FileUploadProps {
  accept: string
  multiple: boolean
  isUploading: boolean
  onFileUpload: (file: File) => void
}

const FileUpload = ({ accept, multiple, isUploading, onFileUpload }: FileUploadProps) => {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const boxBgColor = useColorModeValue('gray.50', 'gray.700')
  const borderColor = useColorModeValue('gray.200', 'gray.600')
  const activeBorderColor = useColorModeValue('blue.500', 'blue.300')

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      setSelectedFile(file)
    }
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setSelectedFile(file)
    }
  }

  const handleButtonClick = () => {
    if (inputRef.current) {
      inputRef.current.click()
    }
  }

  const handleSubmit = () => {
    if (selectedFile) {
      onFileUpload(selectedFile)
    }
  }

  return (
    <FormControl isRequired>
      <VStack spacing={4} align="stretch" width="100%">
        <Box
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          bg={boxBgColor}
          borderWidth="2px"
          borderStyle="dashed"
          borderColor={dragActive ? activeBorderColor : borderColor}
          borderRadius="md"
          p={6}
          textAlign="center"
          cursor="pointer"
          onClick={handleButtonClick}
          transition="all 0.2s"
          _hover={{ borderColor: 'gray.300' }}
        >
          <Input
            ref={inputRef}
            type="file"
            height="100%"
            width="100%"
            position="absolute"
            top="0"
            left="0"
            opacity="0"
            aria-hidden="true"
            accept={accept}
            multiple={multiple}
            onChange={handleChange}
          />
          <VStack spacing={3}>
            <Icon
              boxSize={12}
              color={dragActive ? 'blue.500' : 'gray.400'}
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
              fill="none"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </Icon>
            <Text fontWeight="bold">Drag and drop your file here</Text>
            <Text fontSize="sm">or click to browse</Text>
            {selectedFile && <Text color="green.500">{selectedFile.name}</Text>}
          </VStack>
        </Box>

        <Button
          colorScheme="blue"
          isLoading={isUploading}
          loadingText="Uploading..."
          isDisabled={!selectedFile || isUploading}
          onClick={handleSubmit}
        >
          Upload PCB File
        </Button>
      </VStack>
    </FormControl>
  )
}

export default FileUpload 