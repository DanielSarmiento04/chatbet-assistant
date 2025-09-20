# ChatBet Assistant Backend

Un backend de IA conversacional basado en FastAPI para información y recomendaciones de apuestas deportivas.

## Descripción General

ChatBet Assistant es una API conversacional inteligente que proporciona información de apuestas deportivas en tiempo real, análisis de cuotas y recomendaciones de apuestas. Construido con FastAPI, se integra con APIs deportivas externas y utiliza Google Gemini AI para procesamiento de lenguaje natural.

## Características

- Integración de datos deportivos en tiempo real
- Análisis de cuotas y recomendaciones de apuestas
- Soporte WebSocket para chat en vivo
- Clasificación de intenciones y gestión de conversaciones
- Información de torneos y partidos
- Autenticación de usuarios y gestión de sesiones
- Manejo integral de errores y respuestas de respaldo

## Stack Tecnológico

- **Framework**: FastAPI
- **IA/LLM**: Google Gemini AI
- **Lenguaje**: Python 3.11+
- **Base de Datos**: Redis (para caché)
- **WebSocket**: Soporte WebSocket de FastAPI
- **API Externa**: ChatBet Sports API
- **Despliegue**: Docker

## Estructura del Proyecto

```
backend/
├── app/
│   ├── api/                 # Controladores de rutas API
│   ├── core/               # Funcionalidad central (config, auth, logging)
│   ├── models/             # Modelos Pydantic
│   ├── services/           # Servicios de lógica de negocio
│   ├── routes/             # Controladores de rutas legacy
│   └── utils/              # Funciones utilitarias
├── Dockerfile              # Configuración Docker
├── requirements.txt        # Dependencias Python
├── main.py                # Punto de entrada de la aplicación
└── start.sh               # Script de inicio para desarrollo
```

## Instalación

### Prerrequisitos

- Python 3.11 o superior
- Servidor Redis
- Clave API de Google AI

### Configuración

1. Clonar el repositorio
2. Navegar al directorio backend
3. Ejecutar el script de configuración:

```bash
chmod +x setup-env.sh
./setup-env.sh
```

4. Crear un archivo `.env` con tu configuración:

```bash
GOOGLE_API_KEY=tu_clave_api_google_ai
REDIS_HOST=localhost
REDIS_PORT=6379
DEBUG=true
ENVIRONMENT=development
```

5. Iniciar el servidor de desarrollo:

```bash
chmod +x start.sh
./start.sh
```

## Endpoints de la API

### API REST

- `GET /` - Información de la API
- `GET /health/` - Verificación de salud
- `POST /api/v1/chat/message` - Enviar mensaje de chat
- `GET /api/v1/chat/history/{session_id}` - Obtener historial de conversación

### WebSocket

- `ws://localhost:8000/ws/chat` - Chat en tiempo real
- `ws://localhost:8000/ws/sports-updates` - Actualizaciones deportivas en vivo
- `ws://localhost:8000/ws/test` - Página de prueba WebSocket

## Uso

### Ejemplo de API REST

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son los partidos de la Premier League de hoy?",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

### Ejemplo de WebSocket

Conectar a `ws://localhost:8000/ws/chat` y enviar:

```json
{
  "type": "user_message",
  "content": "Muéstrame los partidos de la Champions League",
  "session_id": "tu-session-id",
  "user_id": "tu-user-id"
}
```

## Configuración

Opciones de configuración principales en `.env`:

- `GOOGLE_API_KEY` - Clave API de Google AI (requerida)
- `CHATBET_API_BASE_URL` - URL de la API deportiva externa
- `REDIS_HOST` - Host del servidor Redis
- `DEBUG` - Habilitar modo debug
- `CORS_ORIGINS` - Orígenes CORS permitidos

## Desarrollo

### Ejecutar Pruebas

```bash
python -m pytest test_basic.py
python test_conversation_fix.py
```

### Estructura del Código

- **Servicios**: Lógica de negocio separada en servicios enfocados
- **Modelos**: Modelos Pydantic para seguridad de tipos y validación
- **Capas API**: Separación limpia entre APIs REST y WebSocket
- **Manejo de Errores**: Manejo integral de errores con respuestas de respaldo

## Despliegue con Docker

```bash
docker build -t chatbet-backend .
docker run -p 8000:8000 --env-file .env chatbet-backend
```

## Monitoreo

- Endpoint de salud: `GET /health/ping`
- Estado WebSocket: `GET /ws/status`
- Métricas de rendimiento disponibles a través de logs

## Contribuir

1. Seguir las directrices de estilo Python PEP 8
2. Agregar pruebas para nuevas características
3. Actualizar documentación para cambios en la API
4. Asegurar que todas las pruebas pasen antes de enviar

## Licencia

Este proyecto es parte de una evaluación técnica.

## Soporte

Para problemas y preguntas, consulta la documentación del código y los logs de errores.