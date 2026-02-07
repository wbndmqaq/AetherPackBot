/**
 * AetherPackBot API Client
 * Handles all API communication with the backend
 */

const API = {
    baseURL: '',
    
    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };
        
        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },
    
    /**
     * GET request
     */
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    /**
     * POST request
     */
    post(endpoint, body) {
        return this.request(endpoint, { method: 'POST', body });
    },
    
    /**
     * PUT request
     */
    put(endpoint, body) {
        return this.request(endpoint, { method: 'PUT', body });
    },
    
    /**
     * DELETE request
     */
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },
    
    // ============================================
    // Health Endpoints
    // ============================================
    
    /**
     * Check API health
     */
    async checkHealth() {
        return this.get('/health');
    },
    
    /**
     * Check if service is ready
     */
    async checkReady() {
        return this.get('/ready');
    },
    
    // ============================================
    // Plugins Endpoints
    // ============================================
    
    /**
     * Get all plugins
     */
    async getPlugins() {
        return this.get('/api/plugins');
    },
    
    /**
     * Get plugin details
     */
    async getPlugin(name) {
        return this.get(`/api/plugins/${name}`);
    },
    
    /**
     * Reload a plugin
     */
    async reloadPlugin(name) {
        return this.post(`/api/plugins/${name}/reload`);
    },
    
    // ============================================
    // Platforms Endpoints
    // ============================================
    
    /**
     * Get all platforms
     */
    async getPlatforms() {
        return this.get('/api/platforms');
    },
    
    /**
     * Get platform details
     */
    async getPlatform(name) {
        return this.get(`/api/platforms/${name}`);
    },
    
    /**
     * Reconnect a platform
     */
    async reconnectPlatform(name) {
        return this.post(`/api/platforms/${name}/reconnect`);
    },
    
    // ============================================
    // Providers Endpoints
    // ============================================
    
    /**
     * Get all providers
     */
    async getProviders() {
        return this.get('/api/providers');
    },
    
    /**
     * Get provider details
     */
    async getProvider(name) {
        return this.get(`/api/providers/${name}`);
    },
    
    // ============================================
    // Chat Endpoints
    // ============================================
    
    /**
     * Send a chat message
     */
    async chat(options) {
        const body = {
            message: options.message,
            provider: options.provider || null,
            model: options.model || null,
            system_prompt: options.systemPrompt || null,
            stream: false,
            temperature: options.temperature || null,
            max_tokens: options.maxTokens || null,
        };
        return this.post('/api/chat', body);
    },
    
    /**
     * Stream a chat message (returns async generator)
     */
    async *chatStream(options) {
        const body = {
            message: options.message,
            provider: options.provider || null,
            model: options.model || null,
            system_prompt: options.systemPrompt || null,
            stream: true,
            temperature: options.temperature || null,
            max_tokens: options.maxTokens || null,
        };
        
        const response = await fetch(`${this.baseURL}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') return;
                    if (data.startsWith('[ERROR]')) {
                        throw new Error(data.slice(8));
                    }
                    yield data;
                }
            }
        }
    },
    
    // ============================================
    // Config Endpoints
    // ============================================
    
    /**
     * Get current config
     */
    async getConfig() {
        return this.get('/api/config');
    },
    
    /**
     * Update config
     */
    async updateConfig(config) {
        return this.post('/api/config', { content: config });
    },
    
    /**
     * Reload config from file
     */
    async reloadConfig() {
        return this.post('/api/config/reload');
    },
    
    // ============================================
    // System Endpoints
    // ============================================
    
    /**
     * Get system info
     */
    async getSystemInfo() {
        return this.get('/api/system/info');
    },
    
    /**
     * Get logs
     */
    async getLogs(options = {}) {
        const params = new URLSearchParams();
        if (options.level) params.set('level', options.level);
        if (options.limit) params.set('limit', options.limit);
        const query = params.toString();
        return this.get(`/api/system/logs${query ? '?' + query : ''}`);
    },
};

// Export for use in other scripts
window.API = API;
