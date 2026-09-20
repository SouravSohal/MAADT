import { TelemetryPacket } from "../types/telemetry";
import { BASELINE_TELEMETRY } from "../data/mockTelemetry";

type TelemetryCallback = (data: TelemetryPacket) => void;
type ConnectionCallback = (connected: boolean) => void;

export class TelemetryService {
  private ws: WebSocket | null = null;
  private isConnected = false;
  private callbacks: Set<TelemetryCallback> = new Set();
  private connectionCallbacks: Set<ConnectionCallback> = new Set();
  private mockTimer: NodeJS.Timeout | null = null;
  private mockPacket: TelemetryPacket = { ...BASELINE_TELEMETRY };
  private timeOffset = 0;

  constructor() {
    this.initWebSocket();
  }

  public subscribe(cb: TelemetryCallback): () => void {
    this.callbacks.add(cb);
    // Send immediate packet
    cb(this.mockPacket);
    return () => this.callbacks.delete(cb);
  }

  public subscribeConnection(cb: ConnectionCallback): () => void {
    this.connectionCallbacks.add(cb);
    cb(this.isConnected);
    return () => this.connectionCallbacks.delete(cb);
  }

  public getIsConnected(): boolean {
    return this.isConnected;
  }

  public setManualPacket(packet: TelemetryPacket) {
    this.mockPacket = packet;
    this.notifySubscribers(packet);
  }

  private initWebSocket() {
    if (typeof window === "undefined") return;

    try {
      this.ws = new WebSocket("ws://localhost:8000/ws/telemetry");

      this.ws.onopen = () => {
        this.isConnected = true;
        this.stopMockStream();
        this.notifyConnectionSubscribers(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data);
          const data: TelemetryPacket = {
            ...BASELINE_TELEMETRY,
            ...raw,
            timestamp: raw.timestamp || Date.now() / 1000,
            engine_id: raw.engine_id || "UAV-001",
          };
          this.mockPacket = data;
          this.notifySubscribers(data);
        } catch (e) {
          console.error("Failed to parse telemetry message", e);
        }
      };

      this.ws.onerror = () => {
        this.handleDisconnect();
      };

      this.ws.onclose = () => {
        this.handleDisconnect();
      };
    } catch {
      this.handleDisconnect();
    }
  }

  private handleDisconnect() {
    this.isConnected = false;
    this.notifyConnectionSubscribers(false);
    this.startMockStream();
    // Attempt reconnect in 3s
    setTimeout(() => {
      if (!this.isConnected) {
        this.initWebSocket();
      }
    }, 3000);
  }

  private notifyConnectionSubscribers(connected: boolean) {
    this.connectionCallbacks.forEach((cb) => cb(connected));
  }

  private startMockStream() {
    if (this.mockTimer) return;
    // 2 Hz stream (every 500ms)
    this.mockTimer = setInterval(() => {
      this.timeOffset += 0.5;
      const wobble = Math.sin(this.timeOffset * 0.8);
      const microRpm = Math.round(this.mockPacket.rpm + wobble * 8);
      const microEgt = Number((this.mockPacket.egt + Math.cos(this.timeOffset * 0.5) * 0.4).toFixed(1));

      const updated: TelemetryPacket = {
        ...this.mockPacket,
        timestamp: Date.now() / 1000,
        rpm: microRpm,
        egt: microEgt,
        vibration: Number((this.mockPacket.vibration + Math.sin(this.timeOffset * 2.0) * 0.01).toFixed(2)),
      };

      this.mockPacket = updated;
      this.notifySubscribers(updated);
    }, 500);
  }

  private stopMockStream() {
    if (this.mockTimer) {
      clearInterval(this.mockTimer);
      this.mockTimer = null;
    }
  }

  private notifySubscribers(packet: TelemetryPacket) {
    this.callbacks.forEach((cb) => cb(packet));
  }
}

export const telemetryService = new TelemetryService();
