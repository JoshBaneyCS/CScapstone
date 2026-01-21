// =============================================================================
// GAMECANVAS.TSX - WEBSOCKET GAME STREAMING COMPONENT
// =============================================================================
// This component handles the WebSocket connection to the Python game service
// and renders the game frames to a canvas element.
//
// The game service streams:
//   - Binary messages: PNG/JPEG frames to render
//   - Text messages: JSON game events (state changes, game end)
//
// The component sends:
//   - Player input actions (hit, stand, fold, etc.)
// =============================================================================

import { useEffect, useRef, useState, useCallback } from 'react';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface GameCanvasProps {
  /** The session ID for the WebSocket connection */
  sessionId: string;
  /** Callback when the game ends */
  onGameEnd: (result: GameResult) => void;
  /** Callback when an error occurs */
  onError: (error: string) => void;
  /** The type of game being played */
  gameType: string;
}

export interface GameResult {
  result: string;
  payout_cents: number;
  new_bankroll: number;
  account_deleted?: boolean;
}

interface GameEvent {
  type: string;
  game_ended?: boolean;
  result?: string;
  payout_cents?: number;
  new_bankroll?: number;
  account_deleted?: boolean;
  state?: Record<string, unknown>;
  message?: string;
}

// =============================================================================
// COMPONENT
// =============================================================================

export function GameCanvas({
  sessionId,
  onGameEnd,
  onError,
  gameType
}: GameCanvasProps): JSX.Element {
  // Canvas ref for rendering frames
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);

  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string>('');

  // Game state from server
  const [gameState, setGameState] = useState<Record<string, unknown> | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('Connecting...');

  // -------------------------------------------------------------------------
  // WEBSOCKET CONNECTION
  // -------------------------------------------------------------------------

  useEffect(() => {
    // Determine WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/game/${sessionId}`;

    console.log('Connecting to game WebSocket:', wsUrl);
    setStatusMessage('Connecting to game server...');

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    // Set binary type for receiving frames
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setConnectionError('');
      setStatusMessage('Connected! Waiting for game...');
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Binary data = frame image
        renderFrame(event.data);
        setStatusMessage('');
      } else {
        // Text data = game event
        try {
          const gameEvent: GameEvent = JSON.parse(event.data);
          handleGameEvent(gameEvent);
        } catch (e) {
          console.error('Failed to parse game event:', e);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionError('Connection error');
      onError('Failed to connect to game server');
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      if (event.code !== 1000) {
        // Abnormal close
        const errorMsg = event.reason || 'Connection lost';
        setConnectionError(errorMsg);
        onError(errorMsg);
      }
    };

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmounted');
      }
    };
  }, [sessionId, onError]);

  // -------------------------------------------------------------------------
  // FRAME RENDERING
  // -------------------------------------------------------------------------

  const renderFrame = useCallback((data: ArrayBuffer) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Create blob from binary data
    const blob = new Blob([data], { type: 'image/png' });
    const url = URL.createObjectURL(blob);

    // Load and draw image
    const img = new Image();
    img.onload = () => {
      // Scale image to fit canvas while maintaining aspect ratio
      const scale = Math.min(
        canvas.width / img.width,
        canvas.height / img.height
      );
      const x = (canvas.width - img.width * scale) / 2;
      const y = (canvas.height - img.height * scale) / 2;

      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, x, y, img.width * scale, img.height * scale);

      URL.revokeObjectURL(url);
    };
    img.onerror = () => {
      console.error('Failed to load frame');
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }, []);

  // -------------------------------------------------------------------------
  // GAME EVENT HANDLING
  // -------------------------------------------------------------------------

  const handleGameEvent = useCallback((event: GameEvent) => {
    console.log('Game event:', event);

    if (event.state) {
      setGameState(event.state);
    }

    if (event.message) {
      setStatusMessage(event.message);
    }

    if (event.game_ended) {
      onGameEnd({
        result: event.result || 'unknown',
        payout_cents: event.payout_cents || 0,
        new_bankroll: event.new_bankroll || 0,
        account_deleted: event.account_deleted,
      });
    }
  }, [onGameEnd]);

  // -------------------------------------------------------------------------
  // INPUT HANDLING
  // -------------------------------------------------------------------------

  const sendInput = useCallback((type: string, payload: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'input',
        type,
        payload,
      }));
    } else {
      console.warn('WebSocket not connected, cannot send input');
    }
  }, []);

  // Keyboard input handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent default for game keys
      if (['h', 's', 'd', 'p', 'f', 'c', 'r', 'b'].includes(e.key.toLowerCase())) {
        e.preventDefault();
      }

      switch (e.key.toLowerCase()) {
        case 'h':
          sendInput('hit');
          break;
        case 's':
          sendInput('stand');
          break;
        case 'd':
          sendInput('double');
          break;
        case 'p':
          sendInput('split');
          break;
        case 'f':
          sendInput('fold');
          break;
        case 'c':
          sendInput('call');
          break;
        case 'r':
          sendInput('raise');
          break;
        case 'b':
          sendInput('bet');
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sendInput]);

  // -------------------------------------------------------------------------
  // RENDER
  // -------------------------------------------------------------------------

  // Get game-specific controls
  const getGameControls = () => {
    if (gameType === 'blackjack') {
      return (
        <div className="game-controls blackjack-controls">
          <button onClick={() => sendInput('hit')} className="control-btn">
            Hit (H)
          </button>
          <button onClick={() => sendInput('stand')} className="control-btn">
            Stand (S)
          </button>
          <button onClick={() => sendInput('double')} className="control-btn">
            Double (D)
          </button>
          <button onClick={() => sendInput('split')} className="control-btn">
            Split (P)
          </button>
        </div>
      );
    }

    if (gameType === 'poker') {
      return (
        <div className="game-controls poker-controls">
          <button onClick={() => sendInput('fold')} className="control-btn control-fold">
            Fold (F)
          </button>
          <button onClick={() => sendInput('call')} className="control-btn">
            Call (C)
          </button>
          <button onClick={() => sendInput('raise')} className="control-btn">
            Raise (R)
          </button>
          <button onClick={() => sendInput('bet')} className="control-btn">
            Bet (B)
          </button>
        </div>
      );
    }

    // Default controls
    return (
      <div className="game-controls default-controls">
        <p className="controls-hint">Use keyboard for game controls</p>
      </div>
    );
  };

  return (
    <div className="game-canvas-container">
      {/* Canvas for game rendering */}
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        className="game-canvas"
      />

      {/* Connection overlay */}
      {!isConnected && (
        <div className="game-overlay">
          {connectionError ? (
            <>
              <div className="error-icon">⚠️</div>
              <p className="error-text">{connectionError}</p>
            </>
          ) : (
            <>
              <div className="loading-spinner"></div>
              <p>{statusMessage}</p>
            </>
          )}
        </div>
      )}

      {/* Status message */}
      {isConnected && statusMessage && (
        <div className="game-status-bar">
          <p>{statusMessage}</p>
        </div>
      )}

      {/* Game controls */}
      {isConnected && getGameControls()}

      {/* Keyboard hints */}
      <div className="keyboard-hints">
        <span className="hint-label">Keyboard shortcuts available</span>
      </div>
    </div>
  );
}

export default GameCanvas;
