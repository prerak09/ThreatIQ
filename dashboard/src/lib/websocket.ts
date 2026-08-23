/**
 * ThreatIQ WebSocket Client
 * Real-time transaction streaming from Railway FastAPI Backend
 */

import { WS_BASE_URL, Transaction } from './api';

export type TransactionCallback = (tx: Transaction) => void;
export type StatusCallback = (connected: boolean) => void;

class TransactionStream {
  private socket: WebSocket | null = null;
  private transactionListeners: Set<TransactionCallback> = new Set();
  private statusListeners: Set<StatusCallback> = new Set();
  private reconnectTimeout: any = null;
  private isConnecting: boolean = false;
  private isExplicitlyClosed: boolean = false;

  public connect() {
    if (typeof window === 'undefined') return;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    this.isConnecting = true;
    const wsUrl = `${WS_BASE_URL}/ws/transactions`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnecting = false;
        this.notifyStatus(true);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && (data.id || data.transaction_id || data.amount)) {
            const tx: Transaction = {
              id: data.id || data.transaction_id || `TX-${Date.now()}`,
              transaction_id: data.transaction_id || data.id,
              amount: typeof data.amount === 'number' ? data.amount : 0,
              currency: data.currency || 'USD',
              channel: data.channel || data.auth_channel || 'e-commerce',
              auth_channel: data.auth_channel || data.channel || 'e-commerce',
              attack_type: data.attack_type || data.attack_vector || (data.is_fraud ? 'Adversarial Attack' : 'Normal Payment'),
              attack_vector: data.attack_vector || data.attack_type,
              status: data.status || (data.is_fraud ? (data.blue_team_flagged ? 'detected' : 'missed') : 'approved'),
              timestamp: data.timestamp || Date.now(),
              is_fraud: data.is_fraud ?? false,
              card_last4: data.card_last4 || '4521',
              merchant_id: data.merchant_id || 'MERCH-001',
              blue_team_confidence: data.blue_team_confidence || (data.blue_team_result?.confidence ?? 0.75),
              blue_team_result: data.blue_team_result,
              merchant_result: data.merchant_result,
            };
            this.notifyTransaction(tx);
          }
        } catch (err) {
          console.warn('Failed to parse WebSocket message:', err);
        }
      };

      this.socket.onerror = (err) => {
        console.warn('WebSocket error:', err);
      };

      this.socket.onclose = () => {
        this.notifyStatus(false);
        this.socket = null;
        this.isConnecting = false;
        if (!this.isExplicitlyClosed) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = setTimeout(() => this.connect(), 4000);
        }
      };
    } catch (e) {
      console.warn('WebSocket setup exception:', e);
      this.notifyStatus(false);
      this.isConnecting = false;
      if (!this.isExplicitlyClosed) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = setTimeout(() => this.connect(), 4000);
      }
    }
  }

  public disconnect() {
    this.isExplicitlyClosed = true;
    clearTimeout(this.reconnectTimeout);
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.notifyStatus(false);
  }

  public onTransaction(cb: TransactionCallback): () => void {
    this.transactionListeners.add(cb);
    return () => this.transactionListeners.delete(cb);
  }

  public onStatus(cb: StatusCallback): () => void {
    this.statusListeners.add(cb);
    if (this.socket) {
      cb(this.socket.readyState === WebSocket.OPEN);
    }
    return () => this.statusListeners.delete(cb);
  }

  private notifyTransaction(tx: Transaction) {
    this.transactionListeners.forEach((cb) => {
      try {
        cb(tx);
      } catch (err) {
        console.error('Error in transaction listener:', err);
      }
    });
  }

  private notifyStatus(connected: boolean) {
    this.statusListeners.forEach((cb) => {
      try {
        cb(connected);
      } catch (err) {
        console.error('Error in status listener:', err);
      }
    });
  }
}

export const streamClient = new TransactionStream();
