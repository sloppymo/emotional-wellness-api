/* Dashboard JavaScript Functionality */

// API Configuration
const API_BASE_URL = '/api/v1';
const DASHBOARD_API_URL = '/dashboard/api';

// Configure axios defaults
axios.defaults.headers.common['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Global state
const DashboardState = {
    activeCharts: {},
    updateIntervals: {},
    taskStatuses: new Map(),
    notifications: []
};

// Utility Functions
const Utils = {
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    },
    
    formatDateTime: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString();
    },
    
    formatTime: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString();
    },
    
    formatPercentage: (value) => {
        return `${value.toFixed(1)}%`;
    },
    
    formatNumber: (value) => {
        return new Intl.NumberFormat().format(value);
    },
    
    getStatusColor: (status) => {
        const statusColors = {
            'SUCCESS': 'success',
            'PENDING': 'warning',
            'FAILURE': 'danger',
            'STARTED': 'info',
            'PROGRESS': 'primary'
        };
        return statusColors[status] || 'secondary';
    },
    
    getRiskColor: (risk) => {
        const riskColors = {
            'HIGH': '#e74c3c',
            'MODERATE': '#f39c12',
            'LOW': '#27ae60'
        };
        return riskColors[risk] || '#95a5a6';
    }
};

// Notification System
const NotificationManager = {
    show: (type, message, duration = 5000) => {
        const alertClass = {
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info',
            'success': 'alert-success'
        }[type] || 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        if (duration > 0) {
            setTimeout(() => {
                notification.remove();
            }, duration);
        }
        
        return notification;
    }
};

// Task Management
const TaskManager = {
    submitTask: async (endpoint, data) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/tasks${endpoint}`, data);
            const taskId = response.data.task_id;
            
            // Start monitoring task progress
            TaskManager.monitorTask(taskId);
            
            NotificationManager.show('success', `Task submitted successfully. ID: ${taskId}`);
            return taskId;
        } catch (error) {
            console.error('Error submitting task:', error);
            NotificationManager.show('error', `Failed to submit task: ${error.response?.data?.detail || error.message}`);
            throw error;
        }
    },
    
    monitorTask: (taskId) => {
        const interval = setInterval(async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/tasks/status/${taskId}`);
                const status = response.data;
                
                // Update task status in UI
                TaskManager.updateTaskStatus(taskId, status);
                
                // Stop monitoring if task is complete
                if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(status.status)) {
                    clearInterval(interval);
                    
                    if (status.status === 'SUCCESS') {
                        NotificationManager.show('success', `Task ${taskId} completed successfully`);
                    } else if (status.status === 'FAILURE') {
                        NotificationManager.show('error', `Task ${taskId} failed: ${status.error}`);
                    }
                }
            } catch (error) {
                console.error('Error monitoring task:', error);
                clearInterval(interval);
            }
        }, 2000); // Check every 2 seconds
        
        DashboardState.updateIntervals[taskId] = interval;
    },
    
    updateTaskStatus: (taskId, status) => {
        DashboardState.taskStatuses.set(taskId, status);
        
        // Update any UI elements showing this task
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
            const progressBar = taskElement.querySelector('.progress-bar');
            const statusText = taskElement.querySelector('.task-status');
            
            if (progressBar && status.percent !== undefined) {
                progressBar.style.width = `${status.percent}%`;
                progressBar.textContent = `${status.percent}%`;
            }
            
            if (statusText) {
                statusText.textContent = status.message || status.status;
                statusText.className = `task-status text-${Utils.getStatusColor(status.status)}`;
            }
        }
    }
};

// Chart Management
const ChartManager = {
    createLineChart: (elementId, data, options = {}) => {
        const ctx = document.getElementById(elementId).getContext('2d');
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: options.showLegend || false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: { ...defaultOptions, ...options }
        });
        
        DashboardState.activeCharts[elementId] = chart;
        return chart;
    },
    
    createBarChart: (elementId, data, options = {}) => {
        const ctx = document.getElementById(elementId).getContext('2d');
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: options.showLegend || false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: { ...defaultOptions, ...options }
        });
        
        DashboardState.activeCharts[elementId] = chart;
        return chart;
    },
    
    createDoughnutChart: (elementId, data, options = {}) => {
        const ctx = document.getElementById(elementId).getContext('2d');
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: options.legendPosition || 'bottom'
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: { ...defaultOptions, ...options }
        });
        
        DashboardState.activeCharts[elementId] = chart;
        return chart;
    },
    
    updateChart: (elementId, newData) => {
        const chart = DashboardState.activeCharts[elementId];
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    },
    
    destroyChart: (elementId) => {
        const chart = DashboardState.activeCharts[elementId];
        if (chart) {
            chart.destroy();
            delete DashboardState.activeCharts[elementId];
        }
    }
};

// Data Fetching Functions
const DataService = {
    fetchCrisisTrends: async (period = 'weekly', days = 30) => {
        try {
            const response = await axios.get(`${DASHBOARD_API_URL}/crisis-trends/data`, {
                params: { period, days }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching crisis trends:', error);
            throw error;
        }
    },
    
    fetchRiskStratification: async (cohortSize = 100) => {
        try {
            const response = await axios.get(`${DASHBOARD_API_URL}/risk-stratification/data`, {
                params: { cohort_size: cohortSize }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching risk stratification:', error);
            throw error;
        }
    },
    
    fetchWellnessTrajectories: async (userId = null, cohort = 'all', days = 30) => {
        try {
            const params = { days };
            if (userId) params.user_id = userId;
            else params.cohort = cohort;
            
            const response = await axios.get(`${DASHBOARD_API_URL}/wellness-trajectories/data`, { params });
            return response.data;
        } catch (error) {
            console.error('Error fetching wellness trajectories:', error);
            throw error;
        }
    },
    
    fetchInterventionOutcomes: async (protocolId = null, days = 90) => {
        try {
            const params = { days };
            if (protocolId) params.protocol_id = protocolId;
            
            const response = await axios.get(`${DASHBOARD_API_URL}/intervention-outcomes/data`, { params });
            return response.data;
        } catch (error) {
            console.error('Error fetching intervention outcomes:', error);
            throw error;
        }
    },
    
    fetchEarlyWarnings: async () => {
        try {
            const response = await axios.get(`${DASHBOARD_API_URL}/early-warning-indicators`);
            return response.data;
        } catch (error) {
            console.error('Error fetching early warnings:', error);
            throw error;
        }
    },
    
    fetchDashboardSummary: async () => {
        try {
            const response = await axios.get(`${DASHBOARD_API_URL}/dashboard/summary`);
            return response.data;
        } catch (error) {
            console.error('Error fetching dashboard summary:', error);
            throw error;
        }
    }
};

// Auto-refresh functionality
const AutoRefresh = {
    intervals: {},
    
    start: (key, callback, interval) => {
        if (AutoRefresh.intervals[key]) {
            clearInterval(AutoRefresh.intervals[key]);
        }
        
        // Run immediately
        callback();
        
        // Then run at interval
        AutoRefresh.intervals[key] = setInterval(callback, interval);
    },
    
    stop: (key) => {
        if (AutoRefresh.intervals[key]) {
            clearInterval(AutoRefresh.intervals[key]);
            delete AutoRefresh.intervals[key];
        }
    },
    
    stopAll: () => {
        Object.keys(AutoRefresh.intervals).forEach(key => {
            AutoRefresh.stop(key);
        });
    }
};

// Export for use in other scripts
window.DashboardUtils = {
    Utils,
    NotificationManager,
    TaskManager,
    ChartManager,
    DataService,
    AutoRefresh
}; 