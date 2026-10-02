# MCP: Claude como herramienta (para conectar con Manus)

Este servidor MCP expone dos herramientas que llaman a la API de Anthropic:

- `ask_claude` — una pregunta suelta, sin historial.
- `chat_with_claude` — conversación con varios turnos (mantiene contexto).

## 1. Instalación local

```bash
cd mcp-claude-for-manus
pip install -r requirements.txt
export ANTHROPIC_API_KEY="tu-clave-aqui"
python server.py
```

Esto levanta el servidor en `http://localhost:8000/mcp` usando transporte
`streamable-http` (el que necesitan los clientes remotos como Manus).

## 2. Probarlo antes de conectar Manus

Con el inspector oficial de MCP:

```bash
npx @modelcontextprotocol/inspector
```

Y apunta al `http://localhost:8000/mcp`. Prueba `ask_claude` con un prompt
simple y confirma que responde.

## 3. Desplegarlo para que Manus pueda llegar a él

Manus necesita una **URL pública**, así que localhost no sirve. Opciones
razonables y baratas:

- **Railway** o **Render**: subes el repo, defines `ANTHROPIC_API_KEY` como
  variable de entorno, y te dan una URL tipo `https://tu-app.up.railway.app`.
- **Un VPS propio** (si ya tienes uno) con el proceso corriendo detrás de
  nginx/caddy y HTTPS.
- Para pruebas rápidas sin desplegar nada: un túnel con `ngrok` apuntando a
  tu `localhost:8000` (válido mientras tengas el túnel abierto, no para uso
  serio o a largo plazo).

## 4. Conectar con Manus

En la configuración de conectores/MCP de Manus, añade:

- **URL**: `https://tu-dominio/mcp`
- **Tipo de transporte**: streamable HTTP (o "remote MCP server")
- Sin autenticación adicional si el servidor es privado solo por URL oscura;
  si quieres proteger el endpoint, añade una capa de auth (API key propia,
  no la de Anthropic) delante — eso no viene incluido aquí porque depende de
  dónde lo despliegues.

## Notas

- `ANTHROPIC_API_KEY` es tuya, de tu cuenta de desarrollador en
  console.anthropic.com, y es distinta de tu login en claude.ai. El uso por
  API se cobra aparte (no está incluido en una suscripción de Claude.ai Pro).
- El modelo por defecto es `claude-sonnet-4-6`; puedes cambiarlo pasando el
  parámetro `model` en cada llamada.
- Si en algún momento quieres que el servidor también pueda usar
  herramientas (web search, etc.) dentro de la llamada a Claude, se puede
  añadir, pero la versión actual es deliberadamente simple: texto entra,
  texto sale.
