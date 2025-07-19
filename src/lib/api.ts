/**
 * API service for communicating with the backend
 */

const API_BASE_URL = 'http://localhost:8501/api';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.message || 'An error occurred',
      };
    }
    
    return {
      success: true,
      data: data as T,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Authentication related API calls
 */
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    console.log('Raw login response:', data);
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Login failed',
      };
    }
    
    return {
      success: true,
      data: data.data,
    };
  },
  
  logout: async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        
        return {
          success: response.ok,
          error: !response.ok ? (data.error || 'Logout failed') : undefined,
        };
      } else {
        return { success: response.ok };
      }
    } catch (error) {
      return { success: true };
    }
  },
  
  validateSession: async (token: string) => {
    const response = await fetch(`${API_BASE_URL}/validate_session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    
    const data = await response.json();
    console.log('Raw session validation response:', data);
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Session validation failed',
      };
    }
    
    return {
      success: true,
      data: data.data,
    };
  },
  
  register: async (name: string, email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username: name, 
          email, 
          password 
        }),
      });
      
      const data = await response.json();
      console.log('Raw register response:', data);
      
      if (!response.ok || data.success === false) {
        return {
          success: false,
          error: data.error || 'Registration failed',
        };
      }
      
      return {
        success: true,
        data: data.data || { message: data.message || 'Registration successful' },
      };
    } catch (error) {
      console.error('Registration error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Registration failed',
      };
    }
  },
};

/**
 * User management related API calls
 */
export const userApi = {
  getUsers: async (token: string) => {
    return fetchApi<Array<{
      user_id: number;
      name: string;
      email: string;
      role: string;
      status: string;
    }>>('/users', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },
  
  getPendingUsers: async (token: string) => {
    return fetchApi<Array<{
      user_id: number;
      name: string;
      email: string;
      status: string;
    }>>('/users/pending', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },
  
  approveUser: async (userId: number, token: string) => {
    return fetchApi<{ message: string }>(`/users/${userId}/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },
  
  deleteUser: async (userId: number, token: string) => {
    return fetchApi<{ message: string }>(`/users/${userId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },
};

/**
 * Server resources related API calls
 */
export const resourceApi = {
  getServerResources: async (token: string) => {
    return fetchApi<{
      agents: Array<{
        id: string;
        name: string;
        ip: string;
        status: string;
        resources: {
          cpu: number;
          memory: number;
          gpu: number;
        };
      }>;
    }>('/server-resources', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },
};

/**
 * Admin-specific API calls
 */
export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  container: string;
  containerStatus: string;
  resources: {
    cpu: string;
    ram: string;
    gpu: string;
  };
  server: string;
  serverLocation: string;
  status: string;
}

export interface AdminStats {
  totalUsers: number;
  totalUsersChange: string;
  activeContainers: number;
  containerUtilization: string;
  availableServers: number;
  serverStatus: string;
}

export const adminApi = {
  getAdminUsers: async (token: string) => {
    return fetchApi<{ users: AdminUser[] }>('/admin/users', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getAdminStats: async (token: string) => {
    return fetchApi<{ stats: AdminStats }>('/admin/stats', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  updateUser: async (userId: string, userData: Partial<AdminUser>, token: string) => {
    return fetchApi<{}>(`/admin/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });
  },

  deleteUser: async (userId: string, token: string) => {
    return fetchApi<{}>(`/users/${userId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  approveUser: async (userId: string, server: string, resources: { cpu: string; ram: string; gpu: string }, token: string) => {
    return fetchApi<{}>(`/admin/users/${userId}/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ server, resources }),
    });
  },

  createUser: async (userData: {
    name: string;
    email: string;
    password?: string;
    role: string;
    status: string;
    server: string;
    resources: { cpu: string; ram: string; gpu: string };
  }, token: string) => {
    return fetchApi<{ message: string; defaultPassword: string }>('/admin/users', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });
  },
};
