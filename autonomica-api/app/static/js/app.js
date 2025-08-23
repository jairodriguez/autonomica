// Autonomica Content Management System - Frontend JavaScript
class AutonomicaCMS {
    constructor() {
        this.currentPage = 'dashboard';
        this.apiBaseUrl = '/api/content';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.setupNavigation();
    }

    setupEventListeners() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('main-content');

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            });
        }

        if (mobileSidebarToggle) {
            mobileSidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            });
        }

        // Temperature slider
        const temperatureSlider = document.getElementById('temperature');
        const temperatureValue = document.getElementById('temperature-value');
        if (temperatureSlider && temperatureValue) {
            temperatureSlider.addEventListener('input', (e) => {
                temperatureValue.textContent = e.target.value;
            });
        }

        // Content generation form
        const contentGenerationForm = document.getElementById('content-generation-form');
        if (contentGenerationForm) {
            contentGenerationForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleContentGeneration();
            });
        }

        // Content repurpose form
        const contentRepurposeForm = document.getElementById('content-repurpose-form');
        if (contentRepurposeForm) {
            contentRepurposeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleContentRepurpose();
            });
        }

        // Search functionality
        const searchInput = document.querySelector('input[placeholder="Search content..."]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const pageTitle = document.getElementById('page-title');
        const pageContents = document.querySelectorAll('.page-content');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = link.getAttribute('href').substring(1);
                this.navigateToPage(targetPage);
            });
        });
    }

    navigateToPage(pageName) {
        // Update navigation state
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[href="#${pageName}"]`).classList.add('active');

        // Update page title
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.textContent = this.getPageTitle(pageName);
        }

        // Show/hide page content
        document.querySelectorAll('.page-content').forEach(content => {
            content.classList.add('hidden');
        });
        const targetContent = document.getElementById(pageName);
        if (targetContent) {
            targetContent.classList.remove('hidden');
        }

        this.currentPage = pageName;

        // Load page-specific data
        switch (pageName) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'content-management':
                this.loadContentManagementData();
                break;
            case 'workflow':
                this.loadWorkflowData();
                break;
            case 'analytics':
                this.loadAnalyticsData();
                break;
        }
    }

    getPageTitle(pageName) {
        const titles = {
            'dashboard': 'Dashboard',
            'content-generation': 'Content Generation',
            'content-repurpose': 'Content Repurpose',
            'content-management': 'Content Management',
            'workflow': 'Workflow',
            'analytics': 'Analytics'
        };
        return titles[pageName] || 'Dashboard';
    }

    async loadDashboardData() {
        try {
            // Load dashboard statistics
            const statsResponse = await fetch(`${this.apiBaseUrl}/dashboard/stats`);
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                this.updateDashboardStats(stats);
            }

            // Load recent content
            const recentResponse = await fetch(`${this.apiBaseUrl}/search?limit=5`);
            if (recentResponse.ok) {
                const recentContent = await recentResponse.json();
                this.updateRecentContent(recentContent);
            }

            // Check system health
            const healthResponse = await fetch(`${this.apiBaseUrl}/health`);
            if (healthResponse.ok) {
                const health = await healthResponse.json();
                this.updateSystemHealth(health);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Error loading dashboard data', 'error');
        }
    }

    updateDashboardStats(stats) {
        const totalContent = document.getElementById('total-content');
        const inReviewContent = document.getElementById('in-review-content');
        const approvedContent = document.getElementById('approved-content');
        const publishedContent = document.getElementById('published-content');

        if (totalContent) totalContent.textContent = stats.total_content || 0;
        if (inReviewContent) inReviewContent.textContent = stats.in_review || 0;
        if (approvedContent) approvedContent.textContent = stats.approved || 0;
        if (publishedContent) publishedContent.textContent = stats.published || 0;
    }

    updateRecentContent(content) {
        const recentContentList = document.getElementById('recent-content-list');
        if (!recentContentList) return;

        if (!content || content.length === 0) {
            recentContentList.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-inbox text-4xl mb-4"></i>
                    <p>No content yet</p>
                </div>
            `;
            return;
        }

        const contentItems = content.map(item => `
            <div class="flex items-center justify-between p-4 bg-white rounded-lg border">
                <div class="flex-1">
                    <h4 class="font-medium text-gray-900">${item.title || 'Untitled'}</h4>
                    <p class="text-sm text-gray-600">${item.content_type || 'Unknown type'}</p>
                    <p class="text-xs text-gray-500">${this.formatDate(item.created_at)}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="status-badge status-${this.getStatusClass(item.status)}">${item.status || 'draft'}</span>
                    <button class="text-blue-600 hover:text-blue-800" onclick="cms.viewContent('${item.content_id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
        `).join('');

        recentContentList.innerHTML = contentItems;
    }

    updateSystemHealth(health) {
        const systemHealth = document.getElementById('system-health');
        if (!systemHealth) return;

        const services = [
            { name: 'Versioning Service', key: 'versioning' },
            { name: 'Lifecycle Manager', key: 'lifecycle' },
            { name: 'Quality Orchestrator', key: 'quality' }
        ];

        const healthHTML = services.map(service => {
            const isHealthy = health[service.key] && health[service.key].status === 'healthy';
            const statusClass = isHealthy ? 'status-approved' : 'status-review';
            const statusText = isHealthy ? 'Healthy' : 'Issues';
            
            return `
                <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">${service.name}</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');

        systemHealth.innerHTML = healthHTML;
    }

    async handleContentGeneration() {
        const formData = this.getContentGenerationFormData();
        
        try {
            this.showLoadingState('content-generation-form');
            
            const response = await fetch(`${this.apiBaseUrl}/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                this.displayGeneratedContent(result);
                this.showNotification('Content generated successfully!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to generate content');
            }
        } catch (error) {
            console.error('Error generating content:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.hideLoadingState('content-generation-form');
        }
    }

    getContentGenerationFormData() {
        const contentType = document.getElementById('content-type').value;
        const prompt = document.getElementById('content-prompt').value;
        const brandVoice = document.getElementById('brand-voice').value;
        const temperature = parseFloat(document.getElementById('temperature').value);
        const maxTokens = document.getElementById('max-tokens').value;
        const tags = document.getElementById('content-tags').value;

        // Get selected platforms
        const platformCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');
        const targetPlatforms = Array.from(platformCheckboxes).map(cb => cb.value);

        return {
            content_type: contentType,
            prompt: prompt,
            target_platforms: targetPlatforms,
            brand_voice: brandVoice,
            temperature: temperature,
            max_tokens: maxTokens ? parseInt(maxTokens) : null,
            tags: tags ? tags.split(',').map(tag => tag.trim()) : []
        };
    }

    displayGeneratedContent(content) {
        const generatedContent = document.getElementById('generated-content');
        const contentDisplay = document.getElementById('content-display');

        if (generatedContent && contentDisplay) {
            contentDisplay.innerHTML = `
                <div class="prose max-w-none">
                    <h3 class="text-lg font-semibold mb-2">${content.title || 'Generated Content'}</h3>
                    <div class="text-gray-700 whitespace-pre-wrap">${content.content || content.generated_text || 'No content generated'}</div>
                    ${content.metadata ? `<div class="mt-4 text-sm text-gray-500"><strong>Metadata:</strong> ${JSON.stringify(content.metadata, null, 2)}</div>` : ''}
                </div>
            `;
            generatedContent.classList.remove('hidden');
        }
    }

    async handleContentRepurpose() {
        const formData = this.getContentRepurposeFormData();
        
        try {
            this.showLoadingState('content-repurpose-form');
            
            const response = await fetch(`${this.apiBaseUrl}/repurpose`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                this.displayRepurposedContent(result);
                this.showNotification('Content repurposed successfully!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to repurpose content');
            }
        } catch (error) {
            console.error('Error repurposing content:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.hideLoadingState('content-repurpose-form');
        }
    }

    getContentRepurposeFormData() {
        const sourceContent = document.getElementById('source-content').value;
        const targetFormat = document.getElementById('target-format').value;
        const brandVoice = document.getElementById('repurpose-brand-voice').value;
        const numItems = parseInt(document.getElementById('num-items').value);

        // Get selected platforms
        const platformCheckboxes = document.querySelectorAll('#content-repurpose input[type="checkbox"]:checked');
        const targetPlatforms = Array.from(platformCheckboxes).map(cb => cb.value);

        return {
            source_content: sourceContent,
            source_type: 'blog_post', // Default, could be made dynamic
            target_type: targetFormat,
            target_platforms: targetPlatforms,
            brand_voice: brandVoice,
            num_variations: numItems
        };
    }

    displayRepurposedContent(content) {
        const repurposedContent = document.getElementById('repurposed-content');
        const repurposeDisplay = document.getElementById('repurpose-display');

        if (repurposedContent && repurposeDisplay) {
            let displayHTML = '';
            
            if (content.repurposed_content) {
                content.repurposed_content.forEach((item, index) => {
                    displayHTML += `
                        <div class="bg-gray-50 rounded-lg p-4 border">
                            <h4 class="font-semibold text-gray-800 mb-2">${item.format || 'Repurposed Content'} ${index + 1}</h4>
                            <div class="text-gray-700 whitespace-pre-wrap">${item.content || 'No content'}</div>
                            ${item.platforms ? `<div class="mt-2 text-sm text-gray-500"><strong>Platforms:</strong> ${item.platforms.join(', ')}</div>` : ''}
                        </div>
                    `;
                });
            } else {
                displayHTML = '<p class="text-gray-500">No repurposed content available</p>';
            }

            repurposeDisplay.innerHTML = displayHTML;
            repurposedContent.classList.remove('hidden');
        }
    }

    async loadContentManagementData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/search?limit=50`);
            if (response.ok) {
                const content = await response.json();
                this.updateContentTable(content);
            }
        } catch (error) {
            console.error('Error loading content management data:', error);
            this.showNotification('Error loading content data', 'error');
        }
    }

    updateContentTable(content) {
        const tableBody = document.getElementById('content-table-body');
        if (!tableBody) return;

        if (!content || content.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-12 text-center text-gray-500">
                        <i class="fas fa-inbox text-4xl mb-4 block"></i>
                        <p>No content available</p>
                    </td>
                </tr>
            `;
            return;
        }

        const tableRows = content.map(item => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <i class="fas fa-file-alt text-gray-600"></i>
                            </div>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${item.title || 'Untitled'}</div>
                            <div class="text-sm text-gray-500">${item.content_id}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.content_type || 'Unknown'}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge status-${this.getStatusClass(item.status)}">${item.status || 'draft'}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.author_id || 'Unknown'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${this.formatDate(item.created_at)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div class="flex space-x-2">
                        <button class="text-blue-600 hover:text-blue-900" onclick="cms.viewContent('${item.content_id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="text-green-600 hover:text-green-900" onclick="cms.editContent('${item.content_id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="text-purple-600 hover:text-purple-900" onclick="cms.repurposeContent('${item.content_id}')">
                            <i class="fas fa-recycle"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        tableBody.innerHTML = tableRows;
    }

    async loadWorkflowData() {
        try {
            // Load content by stage
            const stages = ['draft', 'in_review', 'published'];
            const workflowData = {};

            for (const stage of stages) {
                const response = await fetch(`${this.apiBaseUrl}/search?status=${stage}&limit=10`);
                if (response.ok) {
                    const content = await response.json();
                    workflowData[stage] = content;
                }
            }

            this.updateWorkflowColumns(workflowData);
        } catch (error) {
            console.error('Error loading workflow data:', error);
            this.showNotification('Error loading workflow data', 'error');
        }
    }

    updateWorkflowColumns(workflowData) {
        const stages = ['draft', 'in_review', 'published'];
        
        stages.forEach(stage => {
            const column = document.getElementById(`${stage}-column`);
            const countElement = document.getElementById(`${stage}-count`);
            
            if (column && countElement) {
                const content = workflowData[stage] || [];
                countElement.textContent = content.length;

                if (content.length === 0) {
                    column.innerHTML = '<p class="text-gray-500 text-center text-sm">No items</p>';
                } else {
                    const itemsHTML = content.map(item => `
                        <div class="bg-white rounded-lg p-3 border shadow-sm cursor-move" draggable="true" data-content-id="${item.content_id}">
                            <h5 class="font-medium text-sm text-gray-900 mb-1">${item.title || 'Untitled'}</h5>
                            <p class="text-xs text-gray-600 mb-2">${item.content_type || 'Unknown'}</p>
                            <div class="flex items-center justify-between">
                                <span class="text-xs text-gray-500">${this.formatDate(item.created_at)}</span>
                                <div class="flex space-x-1">
                                    <button class="text-blue-600 hover:text-blue-800 text-xs" onclick="cms.viewContent('${item.content_id}')">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="text-green-600 hover:text-green-800 text-xs" onclick="cms.editContent('${item.content_id}')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    
                    column.innerHTML = itemsHTML;
                }
            }
        });

        // Setup drag and drop
        this.setupWorkflowDragAndDrop();
    }

    setupWorkflowDragAndDrop() {
        const draggableItems = document.querySelectorAll('[draggable="true"]');
        const dropZones = document.querySelectorAll('#draft-column, #review-column, #published-column');

        draggableItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.dataset.contentId);
                item.classList.add('opacity-50');
            });

            item.addEventListener('dragend', (e) => {
                item.classList.remove('opacity-50');
            });
        });

        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('bg-blue-50');
            });

            zone.addEventListener('dragleave', (e) => {
                zone.classList.remove('bg-blue-50');
            });

            zone.addEventListener('drop', async (e) => {
                e.preventDefault();
                zone.classList.remove('bg-blue-50');
                
                const contentId = e.dataTransfer.getData('text/plain');
                const newStage = zone.id.replace('-column', '');
                
                try {
                    await this.moveContentToStage(contentId, newStage);
                    this.loadWorkflowData(); // Refresh the workflow
                } catch (error) {
                    this.showNotification('Error moving content', 'error');
                }
            });
        });
    }

    async moveContentToStage(contentId, newStage) {
        // This would typically call an API endpoint to update the content stage
        // For now, we'll just log the action
        console.log(`Moving content ${contentId} to stage ${newStage}`);
        
        // In a real implementation, you would call:
        // await fetch(`${this.apiBaseUrl}/${contentId}/update-stage`, {
        //     method: 'PUT',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ stage: newStage })
        // });
    }

    async loadAnalyticsData() {
        try {
            // Load analytics data from API
            const response = await fetch(`${this.apiBaseUrl}/dashboard/stats`);
            if (response.ok) {
                const stats = await response.json();
                this.updateAnalyticsCharts(stats);
            }
        } catch (error) {
            console.error('Error loading analytics data:', error);
            this.showNotification('Error loading analytics data', 'error');
        }
    }

    updateAnalyticsCharts(stats) {
        // This would typically update charts using a charting library like Chart.js
        // For now, we'll just update the text displays
        console.log('Analytics data loaded:', stats);
    }

    async handleSearch(query) {
        if (query.length < 2) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/search?query=${encodeURIComponent(query)}&limit=10`);
            if (response.ok) {
                const results = await response.json();
                this.displaySearchResults(results);
            }
        } catch (error) {
            console.error('Error searching content:', error);
        }
    }

    displaySearchResults(results) {
        // This would typically show a dropdown or modal with search results
        console.log('Search results:', results);
    }

    // Utility methods
    getStatusClass(status) {
        const statusMap = {
            'draft': 'draft',
            'in_review': 'review',
            'approved': 'approved',
            'published': 'published',
            'archived': 'archived'
        };
        return statusMap[status] || 'draft';
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    showLoadingState(formId) {
        const form = document.getElementById(formId);
        if (form) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
            }
        }
    }

    hideLoadingState(formId) {
        const form = document.getElementById(formId);
        if (form) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.dataset.originalText || 'Submit';
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'success' ? 'bg-green-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Content management methods
    async viewContent(contentId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${contentId}`);
            if (response.ok) {
                const content = await response.json();
                this.showContentModal(content, 'view');
            }
        } catch (error) {
            console.error('Error viewing content:', error);
            this.showNotification('Error loading content', 'error');
        }
    }

    async editContent(contentId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${contentId}`);
            if (response.ok) {
                const content = await response.json();
                this.showContentModal(content, 'edit');
            }
        } catch (error) {
            console.error('Error editing content:', error);
            this.showNotification('Error loading content', 'error');
        }
    }

    async repurposeContent(contentId) {
        // Navigate to repurpose page and pre-fill source content
        this.navigateToPage('content-repurpose');
        
        // Set the source content dropdown
        const sourceContentSelect = document.getElementById('source-content');
        if (sourceContentSelect) {
            sourceContentSelect.value = contentId;
        }
    }

    showContentModal(content, mode) {
        // This would typically show a modal with content details
        // For now, we'll just log the content
        console.log(`${mode} content:`, content);
        
        // In a real implementation, you would create and show a modal
        // with the content details and appropriate actions
    }
}

// Initialize the CMS when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cms = new AutonomicaCMS();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutonomicaCMS;
}




