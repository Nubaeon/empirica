/**
 * Empirica Chat Widget - Embeddable Version
 *
 * Usage:
 *   <script src="https://your-domain.com/widget.js"
 *           data-server="wss://chat.getempirica.com/ws"
 *           data-position="bottom-right"
 *           data-theme="dark">
 *   </script>
 *
 * Or programmatically:
 *   EmpiricaChat.init({ server: 'wss://...', position: 'bottom-right' });
 */

(function() {
  'use strict';

  // Default configuration
  const DEFAULT_CONFIG = {
    server: 'ws://localhost:8080/ws',
    position: 'bottom-right', // bottom-right, bottom-left
    theme: 'dark',
    title: 'Empirica Chat',
    subtitle: 'Epistemic AI Assistant',
    placeholder: 'Ask me anything...',
    welcomeMessage: '🌓 Hello! I\'m Empirica Bot with epistemic memory. Ask me anything!',
    zIndex: 10000
  };

  // CSS styles (scoped to widget)
  const WIDGET_CSS = `
    .empirica-widget-container {
      position: fixed;
      z-index: {{zIndex}};
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .empirica-widget-container.bottom-right {
      bottom: 20px;
      right: 20px;
    }
    .empirica-widget-container.bottom-left {
      bottom: 20px;
      left: 20px;
    }

    /* Toggle Button */
    .empirica-toggle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #238636 0%, #1a7f37 100%);
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .empirica-toggle:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
    .empirica-toggle.open {
      background: #21262d;
    }

    /* Chat Window */
    .empirica-chat-window {
      position: absolute;
      bottom: 70px;
      width: 380px;
      height: 500px;
      background: #0d1117;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      display: none;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid #30363d;
    }
    .empirica-widget-container.bottom-right .empirica-chat-window {
      right: 0;
    }
    .empirica-widget-container.bottom-left .empirica-chat-window {
      left: 0;
    }
    .empirica-chat-window.open {
      display: flex;
    }

    /* Header */
    .empirica-header {
      background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
      padding: 16px;
      border-bottom: 1px solid #30363d;
    }
    .empirica-header h3 {
      margin: 0;
      color: #fff;
      font-size: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .empirica-header p {
      margin: 4px 0 0;
      color: #8b949e;
      font-size: 12px;
    }

    /* Messages */
    .empirica-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }
    .empirica-message {
      margin-bottom: 12px;
      padding: 10px 14px;
      border-radius: 8px;
      max-width: 85%;
      line-height: 1.4;
      font-size: 14px;
      word-wrap: break-word;
    }
    .empirica-message.user {
      background: #238636;
      color: white;
      margin-left: auto;
    }
    .empirica-message.assistant {
      background: #21262d;
      color: #c9d1d9;
      border: 1px solid #30363d;
    }
    .empirica-message.typing {
      color: #58a6ff;
      font-style: italic;
    }

    /* Input */
    .empirica-input-area {
      display: flex;
      padding: 12px;
      background: #161b22;
      border-top: 1px solid #30363d;
      gap: 8px;
    }
    .empirica-input {
      flex: 1;
      padding: 10px 14px;
      border: 1px solid #30363d;
      border-radius: 6px;
      background: #0d1117;
      color: #c9d1d9;
      font-size: 14px;
      outline: none;
    }
    .empirica-input:focus {
      border-color: #58a6ff;
    }
    .empirica-send {
      padding: 10px 16px;
      background: #238636;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
    }
    .empirica-send:hover {
      background: #2ea043;
    }
    .empirica-send:disabled {
      background: #21262d;
      cursor: not-allowed;
    }

    /* Status */
    .empirica-status {
      padding: 6px 12px;
      background: #161b22;
      color: #8b949e;
      font-size: 11px;
      text-align: center;
    }
    .empirica-status.connected { color: #3fb950; }
    .empirica-status.disconnected { color: #f85149; }

    /* Light theme overrides */
    .empirica-widget-container.light .empirica-chat-window {
      background: #fff;
      border-color: #d0d7de;
    }
    .empirica-widget-container.light .empirica-header {
      background: linear-gradient(135deg, #f6f8fa 0%, #fff 100%);
      border-color: #d0d7de;
    }
    .empirica-widget-container.light .empirica-header h3 { color: #24292f; }
    .empirica-widget-container.light .empirica-message.assistant {
      background: #f6f8fa;
      color: #24292f;
      border-color: #d0d7de;
    }
    .empirica-widget-container.light .empirica-input-area {
      background: #f6f8fa;
      border-color: #d0d7de;
    }
    .empirica-widget-container.light .empirica-input {
      background: #fff;
      color: #24292f;
      border-color: #d0d7de;
    }
  `;

  // Widget HTML template
  const WIDGET_HTML = `
    <button class="empirica-toggle" aria-label="Toggle chat">🧠</button>
    <div class="empirica-chat-window">
      <div class="empirica-header">
        <h3>🧠 {{title}}</h3>
        <p>{{subtitle}}</p>
      </div>
      <div class="empirica-messages"></div>
      <div class="empirica-status">Connecting...</div>
      <div class="empirica-input-area">
        <input type="text" class="empirica-input" placeholder="{{placeholder}}">
        <button class="empirica-send">Send</button>
      </div>
    </div>
  `;

  class EmpiricaChat {
    constructor(config = {}) {
      this.config = { ...DEFAULT_CONFIG, ...config };
      this.ws = null;
      this.isOpen = false;
      this.container = null;
      this.messages = [];
    }

    init() {
      this.injectStyles();
      this.createWidget();
      this.bindEvents();
      this.connect();
    }

    injectStyles() {
      const style = document.createElement('style');
      style.textContent = WIDGET_CSS.replace('{{zIndex}}', this.config.zIndex);
      document.head.appendChild(style);
    }

    createWidget() {
      this.container = document.createElement('div');
      this.container.className = `empirica-widget-container ${this.config.position} ${this.config.theme}`;
      this.container.innerHTML = WIDGET_HTML
        .replace('{{title}}', this.config.title)
        .replace('{{subtitle}}', this.config.subtitle)
        .replace('{{placeholder}}', this.config.placeholder);
      document.body.appendChild(this.container);

      // Cache DOM elements
      this.elements = {
        toggle: this.container.querySelector('.empirica-toggle'),
        window: this.container.querySelector('.empirica-chat-window'),
        messages: this.container.querySelector('.empirica-messages'),
        status: this.container.querySelector('.empirica-status'),
        input: this.container.querySelector('.empirica-input'),
        send: this.container.querySelector('.empirica-send')
      };

      // Add welcome message
      this.addMessage(this.config.welcomeMessage, 'assistant');
    }

    bindEvents() {
      this.elements.toggle.addEventListener('click', () => this.toggle());
      this.elements.send.addEventListener('click', () => this.send());
      this.elements.input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') this.send();
      });
    }

    connect() {
      try {
        this.ws = new WebSocket(this.config.server);

        this.ws.onopen = () => {
          this.elements.status.textContent = 'Connected • Epistemic Memory Active';
          this.elements.status.className = 'empirica-status connected';
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'response') {
            this.removeTyping();
            this.addMessage(data.content, 'assistant');
            this.elements.send.disabled = false;
            this.elements.input.disabled = false;
            this.elements.input.focus();
          } else if (data.type === 'typing') {
            this.showTyping(data.content);
          }
        };

        this.ws.onclose = () => {
          this.elements.status.textContent = 'Disconnected';
          this.elements.status.className = 'empirica-status disconnected';
          // Attempt reconnect after 5s
          setTimeout(() => this.connect(), 5000);
        };

        this.ws.onerror = () => {
          this.elements.status.textContent = 'Connection error';
          this.elements.status.className = 'empirica-status disconnected';
        };
      } catch (e) {
        console.error('Empirica Chat: Failed to connect', e);
      }
    }

    toggle() {
      this.isOpen = !this.isOpen;
      this.elements.window.classList.toggle('open', this.isOpen);
      this.elements.toggle.classList.toggle('open', this.isOpen);
      this.elements.toggle.textContent = this.isOpen ? '✕' : '🧠';
      if (this.isOpen) {
        this.elements.input.focus();
      }
    }

    send() {
      const text = this.elements.input.value.trim();
      if (!text || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;

      this.addMessage(text, 'user');
      this.ws.send(JSON.stringify({ message: text }));
      this.elements.input.value = '';
      this.elements.send.disabled = true;
      this.elements.input.disabled = true;
    }

    addMessage(content, role) {
      const div = document.createElement('div');
      div.className = `empirica-message ${role}`;
      // Basic formatting
      div.innerHTML = content
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
      this.elements.messages.appendChild(div);
      this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
      this.messages.push({ role, content });
    }

    showTyping(text) {
      this.removeTyping();
      const div = document.createElement('div');
      div.className = 'empirica-message assistant typing';
      div.textContent = text;
      this.elements.messages.appendChild(div);
      this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    removeTyping() {
      const typing = this.elements.messages.querySelector('.typing');
      if (typing) typing.remove();
    }
  }

  // Auto-initialize from script tag data attributes
  function autoInit() {
    const script = document.currentScript || document.querySelector('script[data-server]');
    if (script) {
      const config = {
        server: script.getAttribute('data-server') || DEFAULT_CONFIG.server,
        position: script.getAttribute('data-position') || DEFAULT_CONFIG.position,
        theme: script.getAttribute('data-theme') || DEFAULT_CONFIG.theme,
        title: script.getAttribute('data-title') || DEFAULT_CONFIG.title
      };
      const chat = new EmpiricaChat(config);
      chat.init();
    }
  }

  // Expose globally
  window.EmpiricaChat = {
    init: function(config) {
      const chat = new EmpiricaChat(config);
      chat.init();
      return chat;
    }
  };

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }
})();
