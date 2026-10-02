"""
MCP server que expone a Claude (vía la API de Anthropic) como una herramienta.
Pensado para que agentes externos (como Manus) se conecten por HTTP y puedan
"preguntarle a Claude" dentro de sus propios flujos.

Requiere:
    pip install "mcp[cli]" anthropic

Variables de entorno:
    ANTHROPIC_API_KEY   -> tu clave de la API de Anthropic (console.anthropic.com)
    MCP_PORT            -> puerto HTTP (por defecto 8000)

Ejecutar:
    python server.py

Una vez desplegado en algún host con URL pública, le das a Manus esa URL
(terminada en /mcp) como servidor MCP remoto.
"""

import os
from typing import Optional

from anthropic import Anthropic
from mcp.server.fastmcp import FastMCP

# --- Configuración ---------------------------------------------------------

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Falta la variable de entorno ANTHROPIC_API_KEY. "
        "Consíguela en https://console.anthropic.com/settings/keys"
    )

client = Anthropic(api_key=API_KEY)

DEFAULT_MODEL = "claude-sonnet-4-6"

mcp = FastMCP(
    name="claude-bridge",
    instructions=(
        "Este servidor da acceso a Claude (Anthropic) como herramienta. "
        "Úsalo cuando necesites razonamiento, redacción, análisis de texto "
        "o una segunda opinión de otro modelo dentro de tu flujo de trabajo."
    ),
)


# --- Herramientas ------------------------------------------------------------

@mcp.tool(
    title="Preguntar a Claude",
    description=(
        "Envía un prompt a Claude (modelo de Anthropic) y devuelve su respuesta "
        "en texto plano. Úsalo para pedir análisis, redacción, resúmenes, "
        "generación de ideas o cualquier tarea de razonamiento en lenguaje natural."
    ),
)
def ask_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> str:
    """
    Args:
        prompt: El mensaje o pregunta que se le quiere hacer a Claude.
        system_prompt: Instrucciones de sistema opcionales (rol, tono, restricciones).
        model: Modelo a usar. Por defecto 'claude-sonnet-4-6'.
        max_tokens: Límite de tokens de salida (por defecto 2048).
    """
    if not prompt or not prompt.strip():
        raise ValueError("El parámetro 'prompt' no puede estar vacío.")

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    try:
        response = client.messages.create(**kwargs)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Error llamando a la API de Anthropic: {exc}. "
            "Revisa que ANTHROPIC_API_KEY sea válida y tenga saldo/cupo disponible."
        ) from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts) if text_parts else "(Claude no devolvió texto)"


@mcp.tool(
    title="Chat con Claude (multi-turno)",
    description=(
        "Igual que 'ask_claude' pero permite mandar un historial de turnos "
        "(usuario/asistente) para mantener contexto de una conversación."
    ),
)
def chat_with_claude(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> str:
    """
    Args:
        messages: Lista de turnos, cada uno con 'role' ('user' o 'assistant')
            y 'content' (texto). Ej: [{"role": "user", "content": "Hola"}]
        system_prompt: Instrucciones de sistema opcionales.
        model: Modelo a usar.
        max_tokens: Límite de tokens de salida.
    """
    if not messages:
        raise ValueError("El parámetro 'messages' no puede estar vacío.")

    kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system_prompt:
        kwargs["system"] = system_prompt

    try:
        response = client.messages.create(**kwargs)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Error llamando a la API de Anthropic: {exc}") from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts) if text_parts else "(Claude no devolvió texto)"


# --- Arranque ----------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", "8000"))
    # streamable-http: transporte remoto, el que necesita Manus para conectarse por URL
    mcp.run(transport="streamable-http", port=port)
