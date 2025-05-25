// Simple Notification API for Orchestra Admin UI
// Handles incoming notifications from health monitor and other services

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 100;
        this.listeners = [];
    }

    // Add a notification
    addNotification(notification) {
        const enrichedNotification = {
            id: Date.now() + Math.random(),
            timestamp: notification.timestamp || new Date().toISOString(),
            message: notification.message,
            level: notification.level || 'info',
            source: notification.source || 'unknown',
            data: notification.data || {},
            read: false
        };

        this.notifications.unshift(enrichedNotification);

        // Keep only the latest notifications
        if (this.notifications.length > this.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.maxNotifications);
        }

        // Notify listeners
        this.listeners.forEach(callback => callback(enrichedNotification));

        return enrichedNotification;
    }

    // Get all notifications
    getAllNotifications() {
        return this.notifications;
    }

    // Get unread notifications
    getUnreadNotifications() {
        return this.notifications.filter(n => !n.read);
    }

    // Mark notification as read
    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.read = true;
        }
    }

    // Clear all notifications
    clearAll() {
        this.notifications = [];
        this.listeners.forEach(callback => callback({ type: 'clear_all' }));
    }

    // Subscribe to notification updates
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }
}

// Global notification manager instance
const notificationManager = new NotificationManager();

// API endpoints for the notification system
export const notificationAPI = {
    // Receive notification from external services (health monitor, etc.)
    receiveNotification: async (notification) => {
        try {
            const addedNotification = notificationManager.addNotification(notification);
            console.log('📨 Notification received:', addedNotification);
            return { success: true, id: addedNotification.id };
        } catch (error) {
            console.error('Failed to add notification:', error);
            return { success: false, error: error.message };
        }
    },

    // Get all notifications
    getNotifications: () => {
        return notificationManager.getAllNotifications();
    },

    // Get unread count
    getUnreadCount: () => {
        return notificationManager.getUnreadNotifications().length;
    },

    // Mark as read
    markAsRead: (id) => {
        notificationManager.markAsRead(id);
        return { success: true };
    },

    // Clear all
    clearAll: () => {
        notificationManager.clearAll();
        return { success: true };
    },

    // Subscribe to updates
    subscribe: (callback) => {
        return notificationManager.subscribe(callback);
    }
};

// Simple HTTP server simulation for receiving notifications
// In a real app, this would be handled by your backend
export const startNotificationServer = () => {
    // This is a mock - in real implementation you'd have an actual endpoint
    console.log('🔔 Notification system initialized');

    // Example: Add some test notifications
    setTimeout(() => {
        notificationAPI.receiveNotification({
            message: "Orchestra services initialized",
            level: "success",
            source: "system",
            data: { services: ["mcp-secret-manager", "orchestrator"] }
        });
    }, 1000);
};

// Mock API endpoint that external services can call
// This simulates the /api/notifications endpoint
export const handleNotificationPost = (requestBody) => {
    try {
        const notification = JSON.parse(requestBody);
        return notificationAPI.receiveNotification(notification);
    } catch (error) {
        return { success: false, error: 'Invalid JSON in request body' };
    }
};

// Utility function to format notification messages
export const formatNotificationMessage = (notification) => {
    const levelEmojis = {
        info: 'ℹ️',
        success: '✅',
        warning: '⚠️',
        error: '❌'
    };

    const emoji = levelEmojis[notification.level] || 'ℹ️';
    const timeStr = new Date(notification.timestamp).toLocaleTimeString();

    return `${emoji} [${timeStr}] ${notification.message}`;
};

export default notificationManager;
