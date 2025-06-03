import { io, Socket } from 'socket.io-client';
import { store } from '../store';
import { updateSearchProgress } from '../store/slices/searchSlice';
import { updateOperatorStatus } from '../store/slices/operatorSlice';

class WebSocketService {
  private socket: Socket | null = null;
  
  connect() {
    this.socket = io(window.location.origin, {
      path: '/ws',
      transports: ['websocket'],
    });
    
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });
    
    this.socket.on('search-progress', (data) => {
      store.dispatch(updateSearchProgress(data));
    });
    
    this.socket.on('operator-update', (data) => {
      store.dispatch(updateOperatorStatus(data));
    });
    
    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
  
  emit(event: string, data: any) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export const wsService = new WebSocketService();
