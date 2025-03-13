/**
 * Pomodoro Timer JavaScript
 * This script implements a Pomodoro timer with task integration.
 */

class PomodoroTimer {
    constructor() {
        // Timer state
        this.isRunning = false;
        this.isBreak = false;
        this.minutes = 25;
        this.seconds = 0;
        this.originalMinutes = 25;
        this.breakMinutes = 5;
        this.longBreakMinutes = 15;
        this.interval = null;
        this.completedSessions = 0;
        this.totalSessions = 4;
        this.currentTaskId = null;
        
        // Element references - will be initialized when DOM loads
        this.timerDisplay = null;
        this.startBtn = null;
        this.pauseBtn = null;
        this.resetBtn = null;
        this.progressBar = null;
        this.sessionDots = null;
        
        // Audio elements
        this.startSound = new Audio('/static/sounds/start.mp3');
        this.pauseSound = new Audio('/static/sounds/pause.mp3');
        this.completeSound = new Audio('/static/sounds/complete.mp3');
        
        // Initialize volume
        this.startSound.volume = 0.5;
        this.pauseSound.volume = 0.5;
        this.completeSound.volume = 0.5;
        
        // Bind methods to prevent 'this' context issues
        this.startTimer = this.startTimer.bind(this);
        this.pauseTimer = this.pauseTimer.bind(this);
        this.resetTimer = this.resetTimer.bind(this);
        this.updateDisplay = this.updateDisplay.bind(this);
        this.updateProgress = this.updateProgress.bind(this);
        this.handleTimerComplete = this.handleTimerComplete.bind(this);
        this.toggleBreak = this.toggleBreak.bind(this);
        this.updateSettings = this.updateSettings.bind(this);
        this.selectTask = this.selectTask.bind(this);
    }
    
    /**
     * Initialize the timer and attach event listeners
     */
    initialize() {
        // Get element references
        this.timerDisplay = document.getElementById('timer-display');
        this.startBtn = document.getElementById('start-timer');
        this.pauseBtn = document.getElementById('pause-timer');
        this.resetBtn = document.getElementById('reset-timer');
        this.progressBar = document.getElementById('timer-progress-bar');
        this.sessionDots = document.querySelectorAll('.session-dot');
        
        // Settings inputs
        this.pomodoroInput = document.getElementById('pomodoro-minutes');
        this.shortBreakInput = document.getElementById('short-break-minutes');
        this.longBreakInput = document.getElementById('long-break-minutes');
        this.sessionsInput = document.getElementById('total-sessions');
        
        // Task integration
        this.taskSelect = document.getElementById('task-select');
        
        // Initialize display
        this.updateDisplay();
        
        // Attach event listeners
        if (this.startBtn) {
            this.startBtn.addEventListener('click', this.startTimer);
        }
        
        if (this.pauseBtn) {
            this.pauseBtn.addEventListener('click', this.pauseTimer);
        }
        
        if (this.resetBtn) {
            this.resetBtn.addEventListener('click', this.resetTimer);
        }
        
        // Settings listeners
        const settingsInputs = [
            this.pomodoroInput,
            this.shortBreakInput,
            this.longBreakInput,
            this.sessionsInput
        ];
        
        settingsInputs.forEach(input => {
            if (input) {
                input.addEventListener('change', this.updateSettings);
            }
        });
        
        // Task selection listener
        if (this.taskSelect) {
            this.taskSelect.addEventListener('change', this.selectTask);
        }
        
        // Setup notification permission
        this.setupNotifications();
    }
    
    /**
     * Start the timer
     */
    startTimer() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.startSound.play().catch(e => console.log('Error playing sound:', e));
        
        // Update UI
        this.timerDisplay.classList.add('running');
        this.timerDisplay.classList.remove('paused');
        
        // Start the interval
        this.interval = setInterval(() => {
            // Decrement time
            if (this.seconds === 0) {
                if (this.minutes === 0) {
                    this.handleTimerComplete();
                    return;
                }
                this.minutes--;
                this.seconds = 59;
            } else {
                this.seconds--;
            }
            
            // Update display and progress
            this.updateDisplay();
            this.updateProgress();
        }, 1000);
        
        // Update task status if a task is selected
        if (this.currentTaskId) {
            this.updateTaskStatus(this.currentTaskId, 'in_progress');
        }
        
        // Trigger event
        this.dispatchTimerEvent('start');
    }
    
    /**
     * Pause the timer
     */
    pauseTimer() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        this.pauseSound.play().catch(e => console.log('Error playing sound:', e));
        
        // Update UI
        this.timerDisplay.classList.remove('running');
        this.timerDisplay.classList.add('paused');
        
        // Clear interval
        clearInterval(this.interval);
        
        // Trigger event
        this.dispatchTimerEvent('pause');
    }
    
    /**
     * Reset the timer
     */
    resetTimer() {
        // Clear interval
        clearInterval(this.interval);
        
        // Reset state
        this.isRunning = false;
        this.minutes = this.isBreak ? 
            (this.completedSessions % this.totalSessions === 0 ? this.longBreakMinutes : this.breakMinutes) : 
            this.originalMinutes;
        this.seconds = 0;
        
        // Update UI
        this.timerDisplay.classList.remove('running', 'paused');
        this.updateDisplay();
        this.updateProgress();
        
        // Trigger event
        this.dispatchTimerEvent('reset');
    }
    
    /**
     * Update the timer display
     */
    updateDisplay() {
        if (!this.timerDisplay) return;
        
        // Format time
        const formattedMinutes = String(this.minutes).padStart(2, '0');
        const formattedSeconds = String(this.seconds).padStart(2, '0');
        
        // Update display
        this.timerDisplay.textContent = `${formattedMinutes}:${formattedSeconds}`;
        
        // Update page title
        document.title = `${formattedMinutes}:${formattedSeconds} - ${this.isBreak ? 'Break' : 'Focus'} | Timetable`;
    }
    
    /**
     * Update the progress bar
     */
    updateProgress() {
        if (!this.progressBar) return;
        
        const totalTime = (this.isBreak ? 
            (this.completedSessions % this.totalSessions === 0 ? this.longBreakMinutes : this.breakMinutes) : 
            this.originalMinutes) * 60;
        const remainingTime = (this.minutes * 60) + this.seconds;
        const progress = ((totalTime - remainingTime) / totalTime) * 100;
        
        // Set the width of the progress bar to match the progress percentage
        this.progressBar.style.width = `${progress}%`;
        
        // Change color based on current state
        const color = this.isBreak 
            ? 'var(--info-color)' 
            : (!this.isRunning ? 'var(--warning-color)' : 'var(--accent-color)');
            
        this.progressBar.style.backgroundColor = color;
    }
    
    /**
     * Handle timer completion
     */
    handleTimerComplete() {
        // Clear interval
        clearInterval(this.interval);
        
        // Play sound
        this.completeSound.play().catch(e => console.log('Error playing sound:', e));
        
        // Show notification
        this.showNotification(
            this.isBreak ? 'Break Complete!' : 'Session Complete!',
            this.isBreak ? 'Time to focus again.' : 'Time for a break!'
        );
        
        // Toggle between focus and break
        this.toggleBreak();
        
        // Update session counter if focus period ended
        if (!this.isBreak) {
            this.completedSessions++;
            this.updateSessionDots();
            
            // Update task completion if all sessions are done
            if (this.completedSessions === this.totalSessions && this.currentTaskId) {
                this.updateTaskStatus(this.currentTaskId, 'completed');
            }
        }
        
        // Reset timer for next session
        this.resetTimer();
        
        // Trigger event
        this.dispatchTimerEvent('complete');
    }
    
    /**
     * Toggle between focus and break
     */
    toggleBreak() {
        this.isBreak = !this.isBreak;
        
        // Update display
        if (this.timerDisplay) {
            if (this.isBreak) {
                this.timerDisplay.classList.add('break');
            } else {
                this.timerDisplay.classList.remove('break');
            }
        }
        
        // Reset time based on break status
        if (this.isBreak) {
            // Determine if it should be a long break
            if (this.completedSessions % this.totalSessions === 0 && this.completedSessions > 0) {
                this.minutes = this.longBreakMinutes;
            } else {
                this.minutes = this.breakMinutes;
            }
        } else {
            this.minutes = this.originalMinutes;
        }
        this.seconds = 0;
        
        // Update display
        this.updateDisplay();
    }
    
    /**
     * Update session dots
     */
    updateSessionDots() {
        if (!this.sessionDots) return;
        
        // Update session dots
        this.sessionDots.forEach((dot, index) => {
            if (index < this.completedSessions) {
                dot.classList.add('completed');
            } else {
                dot.classList.remove('completed');
            }
        });
    }
    
    /**
     * Update timer settings
     */
    updateSettings() {
        // Get values from inputs (with validation)
        if (this.pomodoroInput) {
            this.originalMinutes = Math.max(1, parseInt(this.pomodoroInput.value) || 25);
        }
        
        if (this.shortBreakInput) {
            this.breakMinutes = Math.max(1, parseInt(this.shortBreakInput.value) || 5);
        }
        
        if (this.longBreakInput) {
            this.longBreakMinutes = Math.max(1, parseInt(this.longBreakInput.value) || 15);
        }
        
        if (this.sessionsInput) {
            this.totalSessions = Math.max(1, parseInt(this.sessionsInput.value) || 4);
            
            // Update session dots
            this.createSessionDots();
        }
        
        // Reset timer with new settings
        this.resetTimer();
        
        // Save settings to localStorage
        this.saveSettings();
    }
    
    /**
     * Create session dots based on total sessions
     */
    createSessionDots() {
        const container = document.querySelector('.session-counter');
        if (!container) return;
        
        // Clear existing dots
        container.innerHTML = '';
        
        // Create new dots
        for (let i = 0; i < this.totalSessions; i++) {
            const dot = document.createElement('div');
            dot.className = 'session-dot';
            if (i < this.completedSessions) {
                dot.classList.add('completed');
            }
            container.appendChild(dot);
        }
        
        // Update session dots reference
        this.sessionDots = document.querySelectorAll('.session-dot');
    }
    
    /**
     * Save settings to localStorage
     */
    saveSettings() {
        const settings = {
            pomodoroMinutes: this.originalMinutes,
            shortBreakMinutes: this.breakMinutes,
            longBreakMinutes: this.longBreakMinutes,
            totalSessions: this.totalSessions
        };
        
        localStorage.setItem('pomodoroSettings', JSON.stringify(settings));
    }
    
    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const savedSettings = localStorage.getItem('pomodoroSettings');
        if (!savedSettings) return;
        
        try {
            const settings = JSON.parse(savedSettings);
            
            // Update instance variables
            this.originalMinutes = settings.pomodoroMinutes || 25;
            this.breakMinutes = settings.shortBreakMinutes || 5;
            this.longBreakMinutes = settings.longBreakMinutes || 15;
            this.totalSessions = settings.totalSessions || 4;
            
            // Update input fields if they exist
            if (this.pomodoroInput) this.pomodoroInput.value = this.originalMinutes;
            if (this.shortBreakInput) this.shortBreakInput.value = this.breakMinutes;
            if (this.longBreakInput) this.longBreakInput.value = this.longBreakMinutes;
            if (this.sessionsInput) this.sessionsInput.value = this.totalSessions;
            
            // Reset timer with loaded settings
            this.resetTimer();
            
            // Update session dots
            this.createSessionDots();
        } catch (error) {
            console.error('Error loading Pomodoro settings:', error);
        }
    }
    
    /**
     * Select a task to associate with the timer
     */
    selectTask() {
        if (!this.taskSelect) return;
        
        const selectedOption = this.taskSelect.options[this.taskSelect.selectedIndex];
        this.currentTaskId = selectedOption.value;
        
        // Save to localStorage
        localStorage.setItem('currentPomodoroTask', this.currentTaskId);
        
        // Trigger event
        this.dispatchTimerEvent('taskSelected', { taskId: this.currentTaskId });
    }
    
    /**
     * Update task status in the backend
     * @param {string} taskId - The ID of the task to update
     * @param {string} status - The new status (in_progress or completed)
     */
    updateTaskStatus(taskId, status) {
        // Skip for empty task ID
        if (!taskId || taskId === 'none') return;
        
        // API endpoint based on status
        let endpoint = '';
        if (status === 'in_progress') {
            endpoint = `/api/tasks/start/${taskId}`;
        } else if (status === 'completed') {
            endpoint = `/api/tasks/complete/${taskId}`;
        } else {
            return;
        }
        
        // Send request to update task status
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const message = status === 'completed' 
                    ? 'Task completed successfully!' 
                    : 'Task started';
                
                showToast(message, 'success');
                
                // If task completed, reset current task
                if (status === 'completed') {
                    this.currentTaskId = null;
                    localStorage.removeItem('currentPomodoroTask');
                    
                    // Update select if it exists
                    if (this.taskSelect) {
                        this.taskSelect.value = 'none';
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error updating task status:', error);
            showToast('Error updating task', 'error');
        });
    }
    
    /**
     * Setup browser notifications
     */
    setupNotifications() {
        // Check if browser supports notifications
        if (!('Notification' in window)) {
            console.log('This browser does not support notifications');
            return;
        }
        
        // Request permission if not already granted
        if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission();
        }
    }
    
    /**
     * Show a browser notification
     * @param {string} title - Notification title
     * @param {string} body - Notification body text
     */
    showNotification(title, body) {
        // Check if browser supports notifications and permission is granted
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            // Fallback to toast notification
            this.showToast(title, body);
            return;
        }
        
        // Create and show the notification
        const notification = new Notification(title, {
            body: body,
            icon: '/static/images/pomodoro-icon.png'
        });
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            notification.close();
        }, 5000);
    }
    
    /**
     * Show a toast notification
     * @param {string} title - Toast title
     * @param {string} message - Toast message
     */
    showToast(title, message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'timer-notification';
        toast.innerHTML = `
            <div class="timer-notification-title">${title}</div>
            <div class="timer-notification-message">${message}</div>
        `;
        
        // Add to DOM
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 5000);
    }
    
    /**
     * Dispatch a custom event for the timer
     * @param {string} action - The action that occurred
     * @param {Object} data - Additional data to include
     */
    dispatchTimerEvent(action, data = {}) {
        const event = new CustomEvent('pomodoroTimer', {
            detail: {
                action,
                isBreak: this.isBreak,
                completedSessions: this.completedSessions,
                totalSessions: this.totalSessions,
                currentTaskId: this.currentTaskId,
                ...data
            }
        });
        
        document.dispatchEvent(event);
    }
}

// Initialize timer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const pomodoroTimer = new PomodoroTimer();
    pomodoroTimer.initialize();
    
    // Load saved settings
    pomodoroTimer.loadSettings();
    
    // Load saved task
    const savedTaskId = localStorage.getItem('currentPomodoroTask');
    if (savedTaskId && pomodoroTimer.taskSelect) {
        pomodoroTimer.taskSelect.value = savedTaskId;
        pomodoroTimer.currentTaskId = savedTaskId;
    }
    
    // Make timer available globally for debugging
    window.pomodoroTimer = pomodoroTimer;
});
