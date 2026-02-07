/**
 * AetherPackBot Admin Panel
 * Main Application Script
 */

class AdminPanel {
    constructor() {
        this.currentPage = 'dashboard';
        this.startTime = Date.now();
        this.refreshInterval = null;
        this.theme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    init() {
        this.applyTheme();
        this.bindEvents();
        this.checkConnection();
        this.loadPage('dashboard');
        this.startUptimeCounter();
        
        // Auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshCurrentPage();
        }, 30000);
    }
    
    /**
     * Apply theme to document
     */
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const icon = document.querySelector('#theme-toggle i');
        if (icon) {
            icon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        this.theme = this.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.theme);
        this.applyTheme();
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.loadPage(page);
            });
        });
        
        // Theme toggle
        document.getElementById('theme-toggle')?.addEventListener('click', () => {
            this.toggleTheme();
        });
        
        // Refresh button
        document.getElementById('refresh-btn')?.addEventListener('click', () => {
            this.refreshCurrentPage();
        });
        
        // Chat input
        document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
        
        document.getElementById('send-message')?.addEventListener('click', () => {
            this.sendChatMessage();
        });
        
        // Config buttons
        document.getElementById('save-config')?.addEventListener('click', () => {
            this.saveConfig();
        });
        
        document.getElementById('reload-config')?.addEventListener('click', () => {
            this.reloadConfig();
        });
        
        // Plugin reload all
        document.getElementById('reload-all-plugins')?.addEventListener('click', () => {
            this.reloadAllPlugins();
        });
        
        // Modal close
        document.getElementById('modal-close')?.addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') {
                this.closeModal();
            }
        });
    }
    
    /**
     * Check API connection
     */
    async checkConnection() {
        const statusEl = document.getElementById('connection-status');
        const textEl = statusEl?.querySelector('.status-text');
        
        try {
            const data = await API.checkHealth();
            statusEl?.classList.add('connected');
            statusEl?.classList.remove('disconnected');
            if (textEl) textEl.textContent = '已连接';
            return true;
        } catch (error) {
            statusEl?.classList.add('disconnected');
            statusEl?.classList.remove('connected');
            if (textEl) textEl.textContent = '未连接';
            return false;
        }
    }
    
    /**
     * Load a page
     */
    async loadPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        
        // Update pages
        document.querySelectorAll('.page').forEach(p => {
            p.classList.toggle('active', p.id === `page-${page}`);
        });
        
        // Update title
        const titles = {
            dashboard: '仪表板',
            platforms: '平台管理',
            plugins: '插件管理',
            providers: 'AI 提供商',
            chat: '聊天测试',
            config: '配置管理',
            logs: '日志查看',
        };
        
        document.getElementById('page-title').textContent = titles[page] || page;
        this.currentPage = page;
        
        // Load page data
        await this.loadPageData(page);
    }
    
    /**
     * Load data for a specific page
     */
    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'platforms':
                await this.loadPlatforms();
                break;
            case 'plugins':
                await this.loadPlugins();
                break;
            case 'providers':
                await this.loadProviders();
                break;
            case 'config':
                await this.loadConfig();
                break;
            case 'chat':
                await this.loadChatProviders();
                break;
        }
    }
    
    /**
     * Refresh current page
     */
    async refreshCurrentPage() {
        const btn = document.getElementById('refresh-btn');
        const icon = btn?.querySelector('i');
        
        if (icon) {
            icon.classList.add('fa-spin');
        }
        
        await this.checkConnection();
        await this.loadPageData(this.currentPage);
        
        setTimeout(() => {
            if (icon) icon.classList.remove('fa-spin');
        }, 500);
    }
    
    /**
     * Load dashboard data
     */
    async loadDashboard() {
        try {
            // Load platforms
            const platformsData = await API.getPlatforms();
            document.getElementById('platforms-count').textContent = platformsData.total;
            this.renderPlatformsStatus(platformsData.platforms);
            
            // Load plugins
            const pluginsData = await API.getPlugins();
            document.getElementById('plugins-count').textContent = pluginsData.total;
            this.renderPluginsStatus(pluginsData.plugins);
            
            // Load providers
            try {
                const providersData = await API.getProviders();
                document.getElementById('providers-count').textContent = providersData.total;
            } catch {
                document.getElementById('providers-count').textContent = '0';
            }
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showToast('加载仪表板数据失败', 'error');
        }
    }
    
    /**
     * Render platforms status on dashboard
     */
    renderPlatformsStatus(platforms) {
        const container = document.getElementById('platforms-status');
        
        if (!platforms || platforms.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plug"></i>
                    <p>暂无已注册的平台</p>
                </div>
            `;
            return;
        }
        
        const icons = {
            telegram: 'fab fa-telegram',
            discord: 'fab fa-discord',
        };
        
        container.innerHTML = platforms.map(p => `
            <div class="platform-item">
                <div class="platform-info">
                    <div class="platform-icon ${p.type.toLowerCase()}">
                        <i class="${icons[p.type.toLowerCase()] || 'fas fa-plug'}"></i>
                    </div>
                    <span>${p.name}</span>
                </div>
                <span class="status-badge ${p.connected ? 'connected' : 'disconnected'}">
                    <i class="fas fa-circle" style="font-size: 0.5rem;"></i>
                    ${p.connected ? '已连接' : '未连接'}
                </span>
            </div>
        `).join('');
    }
    
    /**
     * Render plugins status on dashboard
     */
    renderPluginsStatus(plugins) {
        const container = document.getElementById('plugins-status');
        
        if (!plugins || plugins.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-puzzle-piece"></i>
                    <p>暂无已加载的插件</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = plugins.map(p => `
            <div class="plugin-item">
                <div class="plugin-info">
                    <div class="plugin-icon">
                        <i class="fas fa-puzzle-piece"></i>
                    </div>
                    <span>${p.name}</span>
                </div>
                <span class="status-badge ${p.enabled ? 'enabled' : 'disabled'}">
                    ${p.enabled ? '已启用' : '已禁用'}
                </span>
            </div>
        `).join('');
    }
    
    /**
     * Load platforms page
     */
    async loadPlatforms() {
        const container = document.getElementById('platforms-table');
        
        try {
            const data = await API.getPlatforms();
            
            if (!data.platforms || data.platforms.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-plug"></i>
                        <p>暂无已注册的平台</p>
                        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                            在 config.yaml 中配置平台以开始使用
                        </p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>名称</th>
                            <th>类型</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.platforms.map(p => `
                            <tr>
                                <td><strong>${p.name}</strong></td>
                                <td>${p.type}</td>
                                <td>
                                    <span class="status-badge ${p.connected ? 'connected' : 'disconnected'}">
                                        ${p.connected ? '已连接' : '未连接'}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-secondary" onclick="app.reconnectPlatform('${p.name}')">
                                        <i class="fas fa-sync-alt"></i> 重连
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } catch (error) {
            console.error('Failed to load platforms:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>加载平台数据失败</p>
                </div>
            `;
        }
    }
    
    /**
     * Reconnect a platform
     */
    async reconnectPlatform(name) {
        try {
            await API.reconnectPlatform(name);
            this.showToast(`平台 ${name} 重连成功`, 'success');
            await this.loadPlatforms();
        } catch (error) {
            this.showToast(`平台 ${name} 重连失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * Load plugins page
     */
    async loadPlugins() {
        const container = document.getElementById('plugins-grid');
        
        try {
            const data = await API.getPlugins();
            
            if (!data.plugins || data.plugins.length === 0) {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1;">
                        <i class="fas fa-puzzle-piece"></i>
                        <p>暂无已加载的插件</p>
                        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                            将插件文件放入 plugins/ 目录并重启
                        </p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = data.plugins.map(p => `
                <div class="plugin-card">
                    <div class="plugin-header">
                        <span class="plugin-name">${p.name}</span>
                        <span class="plugin-version">${p.version}</span>
                    </div>
                    <p class="plugin-description">${p.description || '暂无描述'}</p>
                    <div class="plugin-actions">
                        <button class="btn btn-sm btn-secondary" onclick="app.reloadPlugin('${p.name}')">
                            <i class="fas fa-sync-alt"></i> 重载
                        </button>
                        <span class="status-badge ${p.enabled ? 'enabled' : 'disabled'}">
                            ${p.enabled ? '已启用' : '已禁用'}
                        </span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load plugins:', error);
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>加载插件数据失败</p>
                </div>
            `;
        }
    }
    
    /**
     * Reload a plugin
     */
    async reloadPlugin(name) {
        try {
            await API.reloadPlugin(name);
            this.showToast(`插件 ${name} 重载成功`, 'success');
            await this.loadPlugins();
        } catch (error) {
            this.showToast(`插件 ${name} 重载失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * Reload all plugins
     */
    async reloadAllPlugins() {
        try {
            const data = await API.getPlugins();
            for (const plugin of data.plugins) {
                await API.reloadPlugin(plugin.name);
            }
            this.showToast('所有插件重载成功', 'success');
            await this.loadPlugins();
        } catch (error) {
            this.showToast(`重载插件失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * Load providers page
     */
    async loadProviders() {
        const container = document.getElementById('providers-grid');
        
        try {
            const data = await API.getProviders();
            
            if (!data.providers || data.providers.length === 0) {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1;">
                        <i class="fas fa-brain"></i>
                        <p>暂无已配置的 AI 提供商</p>
                        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                            在 config.yaml 中配置提供商
                        </p>
                    </div>
                `;
                return;
            }
            
            const icons = {
                openai: 'fas fa-robot',
                anthropic: 'fas fa-brain',
                gemini: 'fas fa-gem',
            };
            
            container.innerHTML = data.providers.map(p => `
                <div class="provider-card">
                    <div class="provider-header">
                        <span class="provider-name">
                            <i class="${icons[p.name.toLowerCase()] || 'fas fa-brain'}"></i>
                            ${p.name}
                        </span>
                        <span class="status-badge enabled">可用</span>
                    </div>
                    <p class="provider-info">
                        模型: ${p.model || '默认'}
                    </p>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load providers:', error);
            // Show placeholder providers
            container.innerHTML = `
                <div class="provider-card">
                    <div class="provider-header">
                        <span class="provider-name">
                            <i class="fas fa-robot"></i>
                            OpenAI
                        </span>
                        <span class="status-badge disabled">未配置</span>
                    </div>
                    <p class="provider-info">GPT-4, GPT-3.5-Turbo</p>
                </div>
                <div class="provider-card">
                    <div class="provider-header">
                        <span class="provider-name">
                            <i class="fas fa-brain"></i>
                            Anthropic
                        </span>
                        <span class="status-badge disabled">未配置</span>
                    </div>
                    <p class="provider-info">Claude 3 Opus, Sonnet, Haiku</p>
                </div>
                <div class="provider-card">
                    <div class="provider-header">
                        <span class="provider-name">
                            <i class="fas fa-gem"></i>
                            Gemini
                        </span>
                        <span class="status-badge disabled">未配置</span>
                    </div>
                    <p class="provider-info">Gemini Pro, Gemini Pro Vision</p>
                </div>
            `;
        }
    }
    
    /**
     * Load chat providers dropdown
     */
    async loadChatProviders() {
        const select = document.getElementById('chat-provider');
        if (!select) return;
        
        try {
            const data = await API.getProviders();
            
            select.innerHTML = '<option value="">默认</option>';
            
            if (data.providers) {
                data.providers.forEach(p => {
                    const option = document.createElement('option');
                    option.value = p.name;
                    option.textContent = p.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Failed to load chat providers:', error);
        }
    }
    
    /**
     * Send a chat message
     */
    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        const messagesContainer = document.getElementById('chat-messages');
        
        // Remove welcome message if present
        const welcome = messagesContainer.querySelector('.chat-welcome');
        if (welcome) welcome.remove();
        
        // Add user message
        this.addChatMessage(message, 'user');
        input.value = '';
        
        // Get settings
        const provider = document.getElementById('chat-provider').value || null;
        const model = document.getElementById('chat-model').value || null;
        const systemPrompt = document.getElementById('chat-system-prompt').value || null;
        const temperature = parseFloat(document.getElementById('chat-temperature').value) || null;
        const maxTokens = parseInt(document.getElementById('chat-max-tokens').value) || null;
        
        try {
            const response = await API.chat({
                message,
                provider,
                model,
                systemPrompt,
                temperature,
                maxTokens,
            });
            
            this.addChatMessage(response.content, 'assistant');
        } catch (error) {
            this.addChatMessage(`错误: ${error.message}`, 'assistant');
            this.showToast('发送消息失败', 'error');
        }
    }
    
    /**
     * Add a message to the chat
     */
    addChatMessage(content, role) {
        const container = document.getElementById('chat-messages');
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}`;
        messageEl.innerHTML = this.formatMessage(content);
        container.appendChild(messageEl);
        container.scrollTop = container.scrollHeight;
    }
    
    /**
     * Format message content (basic markdown)
     */
    formatMessage(content) {
        // Escape HTML
        content = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Code blocks
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        
        // Inline code
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    /**
     * Load config
     */
    async loadConfig() {
        const editor = document.getElementById('config-content');
        
        try {
            const data = await API.getConfig();
            editor.value = data.content || '';
        } catch (error) {
            console.error('Failed to load config:', error);
            editor.value = '# 无法加载配置\n# 请确保 API 服务器正在运行并且配置了 /api/config 端点';
        }
    }
    
    /**
     * Save config
     */
    async saveConfig() {
        const editor = document.getElementById('config-content');
        const content = editor.value;
        
        try {
            await API.updateConfig(content);
            this.showToast('配置保存成功', 'success');
        } catch (error) {
            this.showToast(`保存配置失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * Reload config
     */
    async reloadConfig() {
        try {
            await API.reloadConfig();
            await this.loadConfig();
            this.showToast('配置重载成功', 'success');
        } catch (error) {
            this.showToast(`重载配置失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * Start uptime counter
     */
    startUptimeCounter() {
        const updateUptime = () => {
            const elapsed = Date.now() - this.startTime;
            const seconds = Math.floor(elapsed / 1000) % 60;
            const minutes = Math.floor(elapsed / 60000) % 60;
            const hours = Math.floor(elapsed / 3600000);
            
            const uptime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const el = document.getElementById('uptime');
            if (el) el.textContent = uptime;
        };
        
        updateUptime();
        setInterval(updateUptime, 1000);
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle',
        };
        
        toast.innerHTML = `
            <i class="${icons[type] || icons.info}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Remove after 4 seconds
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    
    /**
     * Show modal
     */
    showModal(title, content, onConfirm) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = content;
        document.getElementById('modal-overlay').classList.add('active');
        
        const confirmBtn = document.getElementById('modal-confirm');
        confirmBtn.onclick = () => {
            if (onConfirm) onConfirm();
            this.closeModal();
        };
    }
    
    /**
     * Close modal
     */
    closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    }
}

// Initialize the app
const app = new AdminPanel();
