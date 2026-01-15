/**
 * Menza Native Bridge
 * Handles communication between the web app and native iOS features via Capacitor
 */

// Check if running in Capacitor
const isNative = typeof Capacitor !== 'undefined' && Capacitor.isNativePlatform();
const isIOS = isNative && Capacitor.getPlatform() === 'ios';

// Initialize native features when Capacitor is ready
document.addEventListener('DOMContentLoaded', async () => {
    if (isNative) {
        console.log('Running in Capacitor on:', Capacitor.getPlatform());
        await initializeNativeFeatures();
    } else {
        console.log('Running in web browser');
    }
});

/**
 * Initialize all native features
 */
async function initializeNativeFeatures() {
    // Handle status bar
    if (window.Capacitor?.Plugins?.StatusBar) {
        const { StatusBar, Style } = Capacitor.Plugins;
        try {
            await StatusBar.setStyle({ style: Style.Dark });
            await StatusBar.setBackgroundColor({ color: '#030306' });
        } catch (e) {
            console.log('StatusBar not available');
        }
    }
    
    // Handle keyboard
    if (window.Capacitor?.Plugins?.Keyboard) {
        const { Keyboard } = Capacitor.Plugins;
        Keyboard.addListener('keyboardWillShow', (info) => {
            document.body.style.paddingBottom = info.keyboardHeight + 'px';
        });
        Keyboard.addListener('keyboardWillHide', () => {
            document.body.style.paddingBottom = '0px';
        });
    }
    
    // Initialize push notifications
    await initializePushNotifications();
    
    // Handle app state changes
    if (window.Capacitor?.Plugins?.App) {
        const { App } = Capacitor.Plugins;
        App.addListener('appStateChange', ({ isActive }) => {
            console.log('App state changed. Is active:', isActive);
            if (isActive) {
                // App came to foreground - refresh messages
                if (typeof loadMessages === 'function') {
                    loadMessages();
                }
            }
        });
        
        // Handle back button (Android primarily, but good to have)
        App.addListener('backButton', ({ canGoBack }) => {
            if (!canGoBack) {
                App.exitApp();
            } else {
                window.history.back();
            }
        });
    }
    
    // Add safe area padding for notch/home indicator
    addSafeAreaSupport();
}

/**
 * Initialize Push Notifications
 */
async function initializePushNotifications() {
    if (!window.Capacitor?.Plugins?.PushNotifications) {
        console.log('Push notifications not available');
        return;
    }
    
    const { PushNotifications } = Capacitor.Plugins;
    
    try {
        // Request permission
        const permStatus = await PushNotifications.requestPermissions();
        
        if (permStatus.receive === 'granted') {
            // Register with Apple Push Notification service
            await PushNotifications.register();
        }
        
        // Handle registration success
        PushNotifications.addListener('registration', (token) => {
            console.log('Push registration success, token:', token.value);
            // Send token to your server
            sendPushTokenToServer(token.value);
        });
        
        // Handle registration error
        PushNotifications.addListener('registrationError', (error) => {
            console.error('Push registration failed:', error);
        });
        
        // Handle incoming notifications when app is open
        PushNotifications.addListener('pushNotificationReceived', (notification) => {
            console.log('Push notification received:', notification);
            showInAppNotification(notification);
        });
        
        // Handle notification tap
        PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
            console.log('Push notification action:', notification);
            handleNotificationTap(notification);
        });
        
    } catch (e) {
        console.error('Push notification error:', e);
    }
}

/**
 * Send push token to server for storage
 */
async function sendPushTokenToServer(token) {
    try {
        const response = await fetch('/api/push-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token, platform: 'ios' })
        });
        console.log('Push token sent to server');
    } catch (e) {
        console.error('Failed to send push token:', e);
    }
}

/**
 * Show in-app notification
 */
function showInAppNotification(notification) {
    // Create a toast-style notification
    const toast = document.createElement('div');
    toast.className = 'native-notification';
    toast.innerHTML = `
        <strong>${notification.title || 'New Message'}</strong>
        <p>${notification.body || ''}</p>
    `;
    toast.style.cssText = `
        position: fixed;
        top: calc(env(safe-area-inset-top, 0px) + 10px);
        left: 10px;
        right: 10px;
        background: rgba(30, 30, 40, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 12px 16px;
        color: white;
        z-index: 10000;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        animation: slideDown 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/**
 * Handle notification tap
 */
function handleNotificationTap(notification) {
    const data = notification.notification.data;
    if (data?.chatId) {
        // Navigate to specific chat
        window.location.href = `/chat?open=${data.chatId}`;
    } else if (data?.channelId) {
        // Navigate to channel
        window.location.href = `/channel/${data.channelId}`;
    }
}

/**
 * Add safe area support for notch devices
 */
function addSafeAreaSupport() {
    // Add CSS for safe areas
    const style = document.createElement('style');
    style.textContent = `
        body {
            padding-top: env(safe-area-inset-top, 0px);
            padding-bottom: env(safe-area-inset-bottom, 0px);
            padding-left: env(safe-area-inset-left, 0px);
            padding-right: env(safe-area-inset-right, 0px);
        }
        
        .top-nav {
            padding-top: calc(env(safe-area-inset-top, 0px) + 8px) !important;
        }
        
        .input-area, .chat-input-container {
            padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 8px) !important;
        }
        
        @keyframes slideDown {
            from { transform: translateY(-100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        @keyframes slideUp {
            from { transform: translateY(0); opacity: 1; }
            to { transform: translateY(-100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Haptic feedback
 */
async function hapticFeedback(type = 'light') {
    if (!window.Capacitor?.Plugins?.Haptics) return;
    
    const { Haptics, ImpactStyle, NotificationType } = Capacitor.Plugins;
    
    try {
        switch (type) {
            case 'light':
                await Haptics.impact({ style: ImpactStyle.Light });
                break;
            case 'medium':
                await Haptics.impact({ style: ImpactStyle.Medium });
                break;
            case 'heavy':
                await Haptics.impact({ style: ImpactStyle.Heavy });
                break;
            case 'success':
                await Haptics.notification({ type: NotificationType.Success });
                break;
            case 'warning':
                await Haptics.notification({ type: NotificationType.Warning });
                break;
            case 'error':
                await Haptics.notification({ type: NotificationType.Error });
                break;
        }
    } catch (e) {
        console.log('Haptics not available');
    }
}

/**
 * Share content using native share sheet
 */
async function nativeShare(title, text, url) {
    if (!window.Capacitor?.Plugins?.Share) {
        // Fallback to web share API
        if (navigator.share) {
            return navigator.share({ title, text, url });
        }
        return;
    }
    
    const { Share } = Capacitor.Plugins;
    await Share.share({ title, text, url, dialogTitle: 'Share via' });
}

/**
 * Check biometric authentication availability
 */
async function checkBiometricAuth() {
    // This would use a biometric plugin
    // For now, return false
    return false;
}

/**
 * Authenticate with biometrics
 */
async function authenticateWithBiometrics(reason = 'Unlock Menza') {
    // This would use a biometric plugin
    // Implementation depends on the specific plugin used
    return false;
}

// Export functions for use in other scripts
window.NativeBridge = {
    isNative,
    isIOS,
    hapticFeedback,
    nativeShare,
    checkBiometricAuth,
    authenticateWithBiometrics,
    initializePushNotifications
};




