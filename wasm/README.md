# WASM Build (pygbag)

Compiles the Pygame casino GUI to WebAssembly for browser-native rendering.

## Prerequisites

```bash
pip install pygbag
```

## Build

```bash
cd wasm
./build.sh
```

Output goes to `../web/public/game/` (HTML + JS + WASM + assets).

## Local Dev

```bash
cd gui
pygbag .
```

Opens a dev server at `http://localhost:8000`.

## Known pygbag Limitations

- Main loop must be async (`asyncio.run(main())` with `await asyncio.sleep(0)`)
- `requests` library not available — uses `api_client.py` abstraction with `XMLHttpRequest`
- `pygame.FULLSCREEN` may behave differently — canvas size controlled by browser
- File I/O is limited to virtual filesystem
- Some pygame-ce features may not be supported in Emscripten
