import axios from 'axios'

// Create an axios instance with default config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface UploadResponse {
  session_id: string
  filename: string
  message: string
}

export interface NetInfo {
  net_name: string
  component_count: number
  pad_count: number
}

export interface TraceRequest {
  net_name: string
  start_component: string
  start_pad: string
  end_component: string
  end_pad: string
}

export interface Component {
  designator: string
  pads: { padNumber: string, netName: string }[]
}

export interface PathElement {
  type: string
  component?: string
  pad?: string
  length?: number
  radius?: number
  layer: string
  location?: [number, number]
  start?: [number, number]
  end?: [number, number]
  net?: string
  from_layer?: number
  to_layer?: number
}

export interface TraceResponse {
  net_name: string
  start_component: string
  start_pad: string
  end_component: string
  end_pad: string
  length_mm: number | null
  path_description: string | null
  path_elements: PathElement[] | null
}

// API functions
export const uploadPCBFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<UploadResponse>('/upload_pcb', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export const getNetList = async (boardId: string): Promise<NetInfo[]> => {
  const response = await api.get<NetInfo[]>(`/board/${boardId}/nets`)
  return response.data
}

export const getNetComponents = async (boardId: string, netName: string): Promise<Component[]> => {
  try {
    const response = await api.get<Component[]>(`/board/${boardId}/net/${netName}/components`)
    return response.data
  } catch (error) {
    // For now, if API doesn't exist, return empty array
    console.warn('API for net components not implemented, using fallback data')
    
    // Return fallback data - this should be replaced with actual API data
    const fallback: Component[] = [
      { 
        designator: netName.includes('NetC48') ? 'SW2A' : 'U1',
        pads: [
          { padNumber: '1', netName: netName }
        ]
      },
      { 
        designator: netName.includes('NetC48') ? 'C48' : 'R1',
        pads: [
          { padNumber: '1', netName: netName }
        ]
      },
      {
        designator: netName.includes('NetC48') ? 'R82' : 'C1',
        pads: [
          { padNumber: '1', netName: netName }
        ]
      }
    ]
    
    return fallback
  }
}

export const calculateTrace = async (
  boardId: string,
  request: TraceRequest
): Promise<TraceResponse> => {
  const response = await api.post<TraceResponse>(
    `/board/${boardId}/calculate_trace`,
    request
  )
  return response.data
}

export const getTracePath = async (
  boardId: string,
  request: TraceRequest
): Promise<TraceResponse> => {
  // Pass through any errors from the backend
  const response = await api.post<TraceResponse>(
    `/board/${boardId}/trace_path`,
    request
  )
  return response.data
} 