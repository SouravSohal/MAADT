"use client";
import React, { useState, useEffect, useRef } from 'react';
import {
  BrainCircuit,
  X,
  Send,
  Sparkles,
  Bot,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Terminal,
  FileText,
  ChevronDown
} from 'lucide-react';
import { TelemetryPacket } from '../../types/telemetry';
import { apiService } from '../../services/api';

interface AICopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  telemetry: TelemetryPacket;
  initialQuery?: string;
  selectedComponent?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  modelUsed?: string;
}

export default function AICopilotDrawer({
  isOpen,
  onClose,
  telemetry,
  initialQuery,
  selectedComponent,
}: AICopilotDrawerProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'diagnostic'>('chat');
  const [activeModel, setActiveModel] = useState<string>("qwen2.5:3b");
  const [availableModels, setAvailableModels] = useState<string[]>(["qwen2.5:3b", "mistral:latest", "qwen3:14b"]);
  const [ollamaStatus, setOllamaStatus] = useState<"ONLINE" | "OFFLINE">("ONLINE");
  
  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'MAADT Aerospace Propulsion Copilot initialized with local Ollama engine. Live telemetry context linked to AeroPiston-4X Digital Twin. How can I assist with propulsion operations?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      modelUsed: 'qwen2.5:3b',
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Diagnostic Report State
  const [diagnosticReport, setDiagnosticReport] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportTime, setReportTime] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load Ollama status & models
  useEffect(() => {
    async function loadAIStatus() {
      try {
        const res = await apiService.getAIStatus();
        if (res.status === "ONLINE") {
          setOllamaStatus("ONLINE");
          if (res.active_model) setActiveModel(res.active_model);
          if (res.available_models && res.available_models.length > 0) {
            setAvailableModels(res.available_models);
          }
        } else {
          setOllamaStatus("OFFLINE");
        }
      } catch {
        setOllamaStatus("OFFLINE");
      }
    }
    if (isOpen) {
      loadAIStatus();
    }
  }, [isOpen]);

  // Handle initial query if provided
  useEffect(() => {
    if (initialQuery && isOpen) {
      setActiveTab('chat');
      handleSendMessage(initialQuery);
    }
  }, [initialQuery, isOpen]);

  // Scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleModelChange = async (newModel: string) => {
    setActiveModel(newModel);
    try {
      await apiService.selectAIModel(newModel);
    } catch (e) {
      console.error("Failed to switch Ollama model", e);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputMessage;
    if (!query.trim() || isGenerating) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setIsGenerating(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const resp = await apiService.chatAICopilot(query, telemetry, history);

      const botMsg: ChatMessage = {
        role: 'assistant',
        content: resp.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelUsed: resp.model_used || activeModel,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Engine communication error with local Ollama inference service.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          modelUsed: activeModel,
        },
      ]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunDiagnosticReport = async () => {
    setReportLoading(true);
    setDiagnosticReport(null);
    try {
      const resp = await apiService.analyzeDiagnosticsAI(telemetry, telemetry.active_diagnostic);
      setDiagnosticReport(resp.diagnostic_report);
      setReportTime(resp.inference_time_seconds);
    } catch (e) {
      setDiagnosticReport("Failed to generate AI diagnostic report from local Ollama daemon.");
    } finally {
      setReportLoading(false);
    }
  };

  const quickPrompts = [
    "Explain current anomaly and residual divergence",
    "Can the engine sustain current throttle for 45 min?",
    "Evaluate vibration harmonic impact on crankshaft",
    "Assess sensor trust index for EGT and CHT",
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs select-none transition-all font-mono">
      {/* Click outside to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Slide-over Drawer Panel */}
      <div className="w-full max-w-xl bg-[#0D1B2A] border-l border-[#1B344B] flex flex-col h-full shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Top Header */}
        <div className="p-4 bg-[#0B1725] border-b border-[#1B344B] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[#102E4A] border border-[#22AFFF]/40 flex items-center justify-center text-[#22AFFF]">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#F4F7FA]">MAADT AI COPILOT</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                    ollamaStatus === "ONLINE"
                      ? "bg-[#072418] border-[#14532D] text-[#22D88A]"
                      : "bg-[#2D1606] border-[#7C2D12] text-[#FF8A3D]"
                  }`}
                >
                  {ollamaStatus === "ONLINE" ? "LOCAL OLLAMA ONLINE" : "OLLAMA OFFLINE"}
                </span>
              </div>
              <p className="text-[11px] text-[#8FA4B8]">
                Aero-Propulsion Physics Reasoning · localhost:11434
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Model Selector Dropdown */}
            <div className="relative">
              <select
                value={activeModel}
                onChange={(e) => handleModelChange(e.target.value)}
                className="bg-[#101F30] hover:bg-[#1B344B] text-[#22AFFF] border border-[#1B344B] rounded px-2.5 py-1 text-xs font-bold cursor-pointer transition-colors focus:outline-hidden"
              >
                {availableModels.map((m) => (
                  <option key={m} value={m} className="bg-[#0D1B2A] text-[#F4F7FA]">
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 hover:bg-[#101F30] rounded text-[#8FA4B8] hover:text-[#F4F7FA] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Toolbar */}
        <div className="flex border-b border-[#1B344B] bg-[#07111D] px-4 shrink-0">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-4 py-2.5 text-xs font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
              activeTab === 'chat'
                ? "border-[#22AFFF] text-[#22AFFF] bg-[#0B1725]"
                : "border-transparent text-[#8FA4B8] hover:text-[#F4F7FA]"
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Propulsion Chat Copilot</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('diagnostic');
              if (!diagnosticReport) handleRunDiagnosticReport();
            }}
            className={`px-4 py-2.5 text-xs font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
              activeTab === 'diagnostic'
                ? "border-[#22AFFF] text-[#22AFFF] bg-[#0B1725]"
                : "border-transparent text-[#8FA4B8] hover:text-[#F4F7FA]"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>AI Diagnostic Report</span>
          </button>
        </div>

        {/* Live Context Strip */}
        <div className="px-4 py-2 bg-[#0B1725]/80 border-b border-[#1B344B] text-[11px] text-[#8FA4B8] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <span>RPM: <strong className="text-[#F4F7FA]">{Math.round(telemetry.rpm)}</strong></span>
            <span>CHT: <strong className="text-[#F4F7FA]">{Math.round(telemetry.cht)}°C</strong></span>
            <span>EGT: <strong className="text-[#F4F7FA]">{Math.round(telemetry.egt)}°C</strong></span>
            <span>VIB: <strong className="text-[#F4F7FA]">{telemetry.vibration.toFixed(2)}g</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span>Health: <strong className="text-[#22D88A]">{Math.round(telemetry.health_index)}%</strong></span>
            <span>Margin: <strong className="text-[#22AFFF]">{Math.round(telemetry.mission_margin)}%</strong></span>
          </div>
        </div>

        {/* ================= TAB 1: INTERACTIVE COPILOT CHAT ================= */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5 min-h-0">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1.5 text-[10px] text-[#60758A] mb-1">
                    {msg.role === 'assistant' ? (
                      <>
                        <Bot className="w-3 h-3 text-[#22AFFF]" />
                        <span className="font-bold text-[#8FA4B8]">AI Copilot ({msg.modelUsed || activeModel})</span>
                      </>
                    ) : (
                      <span className="font-bold text-[#8FA4B8]">Flight Engineer</span>
                    )}
                    <span>· {msg.timestamp}</span>
                  </div>

                  <div
                    className={`max-w-[85%] p-3 rounded-xl text-xs leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-[#102E4A] border border-[#22AFFF]/40 text-[#F4F7FA]'
                        : 'bg-[#0B1725] border border-[#1B344B] text-[#F4F7FA]'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  </div>
                </div>
              ))}

              {isGenerating && (
                <div className="flex items-center gap-2 text-xs text-[#22AFFF] bg-[#0B1725] p-3 rounded-xl border border-[#1B344B] w-fit">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Inference processing via local {activeModel}...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Prompt Chips */}
            <div className="px-4 py-2 border-t border-[#1B344B] bg-[#0B1725]/50 flex gap-1.5 overflow-x-auto shrink-0">
              {quickPrompts.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(prompt)}
                  disabled={isGenerating}
                  className="px-2.5 py-1 bg-[#101F30] hover:bg-[#102E4A] text-[#8FA4B8] hover:text-[#22AFFF] border border-[#1B344B] rounded text-[10px] whitespace-nowrap transition-colors cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-[#0B1725] border-t border-[#1B344B] flex items-center gap-2 shrink-0">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSendMessage();
                }}
                placeholder="Ask AI Copilot about engine telemetry, physics, or mission risks..."
                disabled={isGenerating}
                className="flex-1 bg-[#07111D] border border-[#1B344B] focus:border-[#22AFFF]/60 rounded-lg px-3 py-2 text-xs text-[#F4F7FA] placeholder-[#60758A] focus:outline-hidden"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={isGenerating || !inputMessage.trim()}
                className="p-2.5 bg-[#102E4A] hover:bg-[#1B4D7E] text-[#22AFFF] disabled:opacity-40 rounded-lg border border-[#22AFFF]/40 transition-colors cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ================= TAB 2: DEEP DIAGNOSTIC REPORT ================= */}
        {activeTab === 'diagnostic' && (
          <div className="flex-1 flex flex-col p-4 overflow-y-auto min-h-0 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-[#F4F7FA]">Deep Diagnostic Reasoning</h4>
                <p className="text-[11px] text-[#8FA4B8]">Grounded in thermodynamic state residuals & sensor trust</p>
              </div>
              <button
                onClick={handleRunDiagnosticReport}
                disabled={reportLoading}
                className="px-3 py-1.5 bg-[#102E4A] hover:bg-[#1B4D7E] text-[#22AFFF] rounded-lg border border-[#22AFFF]/40 text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reportLoading ? 'animate-spin' : ''}`} />
                <span>Re-Analyze</span>
              </button>
            </div>

            {reportLoading && (
              <div className="p-8 flex flex-col items-center justify-center gap-3 bg-[#0B1725] border border-[#1B344B] rounded-xl text-[#22AFFF]">
                <RefreshCw className="w-6 h-6 animate-spin" />
                <span className="text-xs">Generating deep diagnostic synthesis using local {activeModel}...</span>
              </div>
            )}

            {diagnosticReport && !reportLoading && (
              <div className="p-4 bg-[#0B1725] border border-[#1B344B] rounded-xl text-xs space-y-3">
                <div className="flex justify-between items-center text-[10px] text-[#8FA4B8] pb-2 border-b border-[#1B344B]">
                  <span>Model: <strong className="text-[#22AFFF]">{activeModel}</strong></span>
                  {reportTime && <span>Inference Time: <strong className="text-[#F4F7FA]">{reportTime}s</strong></span>}
                </div>
                <div className="whitespace-pre-wrap leading-relaxed text-[#F4F7FA]/90">
                  {diagnosticReport}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
