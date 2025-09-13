import { useEffect, useState, useCallback } from 'react';
import socketService from '../services/socketService';
import { useAuth } from '../context/AuthContext';

export const useSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    // Only connect if user is authenticated
    if (user && !socketService.isSocketConnected()) {
      const connectSocket = async () => {
        try {
          await socketService.connect();
          setIsConnected(true);
          setConnectionError(null);
        } catch (error) {
          setConnectionError(error.message);
          setIsConnected(false);
        }
      };

      connectSocket();
    }

    // Disconnect when user logs out
    if (!user && socketService.isSocketConnected()) {
      socketService.disconnect();
      setIsConnected(false);
    }

    return () => {
      // Cleanup on unmount
      if (!user) {
        socketService.disconnect();
      }
    };
  }, [user]);

  return {
    isConnected,
    connectionError,
    socket: socketService
  };
};

export const useJobProgress = (jobId) => {
  const [progress, setProgress] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const { socket, isConnected } = useSocket();

  const startListening = useCallback(() => {
    if (isConnected && jobId && !isListening) {
      // Join job room
      socket.joinJobRoom(jobId);
      
      // Listen for progress updates
      socket.onJobProgress((data) => {
        if (data.job_id === jobId) {
          setProgress(data);
        }
      });
      
      setIsListening(true);
    }
  }, [socket, isConnected, jobId, isListening]);

  const stopListening = useCallback(() => {
    if (isConnected && jobId && isListening) {
      // Leave job room
      socket.leaveJobRoom(jobId);
      
      // Stop listening for progress updates
      socket.offJobProgress();
      
      setIsListening(false);
      setProgress(null);
    }
  }, [socket, isConnected, jobId, isListening]);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      stopListening();
    };
  }, [stopListening]);

  return {
    progress,
    isListening,
    startListening,
    stopListening
  };
};