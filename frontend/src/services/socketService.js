import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.callbacks = new Map();
  }

  connect(backendUrl = process.env.REACT_APP_BACKEND_URL) {
    if (this.socket && this.isConnected) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        // Create socket connection
        this.socket = io(backendUrl, {
          transports: ['websocket', 'polling'],
          timeout: 20000,
          forceNew: true
        });

        // Connection successful
        this.socket.on('connect', () => {
          console.log('🔌 Socket connected:', this.socket.id);
          this.isConnected = true;
          resolve();
        });

        // Connection error
        this.socket.on('connect_error', (error) => {
          console.error('❌ Socket connection error:', error);
          this.isConnected = false;
          reject(error);
        });

        // Disconnection
        this.socket.on('disconnect', (reason) => {
          console.log('🔌 Socket disconnected:', reason);
          this.isConnected = false;
        });

        // Server confirmation
        this.socket.on('connected', (data) => {
          console.log('✅ Server confirmed connection:', data);
        });

      } catch (error) {
        console.error('❌ Socket connection failed:', error);
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.callbacks.clear();
      console.log('🔌 Socket disconnected manually');
    }
  }

  // Job-specific methods
  joinJobRoom(jobId) {
    if (this.socket && this.isConnected) {
      this.socket.emit('join_job_room', { job_id: jobId });
      console.log(`🏠 Joined job room: ${jobId}`);
    }
  }

  leaveJobRoom(jobId) {
    if (this.socket && this.isConnected) {
      this.socket.emit('leave_job_room', { job_id: jobId });
      console.log(`🏠 Left job room: ${jobId}`);
    }
  }

  // Listen for job progress updates
  onJobProgress(callback) {
    if (this.socket) {
      this.socket.on('job_progress', callback);
      this.callbacks.set('job_progress', callback);
    }
  }

  offJobProgress() {
    if (this.socket) {
      const callback = this.callbacks.get('job_progress');
      if (callback) {
        this.socket.off('job_progress', callback);
        this.callbacks.delete('job_progress');
      }
    }
  }

  // Generic event listeners
  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
      this.callbacks.set(event, callback);
    }
  }

  off(event) {
    if (this.socket) {
      const callback = this.callbacks.get(event);
      if (callback) {
        this.socket.off(event, callback);
        this.callbacks.delete(event);
      }
    }
  }

  emit(event, data) {
    if (this.socket && this.isConnected) {
      this.socket.emit(event, data);
    }
  }

  // Check connection status
  isSocketConnected() {
    return this.socket && this.isConnected;
  }
}

// Create and export singleton instance
const socketService = new SocketService();
export default socketService;