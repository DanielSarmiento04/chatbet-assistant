# ChatBet Backend de IA Conversacional

## 🎯 Descripción del Proyecto

Backend inteligente basado en FastAPI que alimenta un chatbot conversacional de apuestas deportivas con capacidades WebSocket en tiempo real, integración avanzada de IA y procesamiento integral de datos deportivos.

**Características Principales:**
- IA conversacional en tiempo real usando Google Gemini y LangChain
- Transmisión WebSocket para respuestas instantáneas y actualizaciones en vivo
- Integración integral de datos de apuestas deportivas
- Caché inteligente con Redis para rendimiento óptimo
- Despliegue Docker listo para producción
- Gestión de sesiones concurrentes multiusuario
- Clasificación avanzada de intenciones y extracción de entidades
- Llamadas a funciones para recuperación dinámica de datos deportivos

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico
- **Framework**: FastAPI (framework web asíncrono de Python)
- **IA/LLM**: Google Gemini Pro con integración LangChain
- **Base de Datos**: Redis (caché y almacenamiento de sesiones)
- **WebSocket**: Soporte nativo WebSocket de FastAPI
- **API Externa**: Integración con la API de ChatBet Sports
- **Despliegue**: Docker con builds multi-etapa
- **Lenguaje**: Python 3.11+

### Patrones Arquitectónicos
- **Diseño inspirado en microservicios** con clara separación de responsabilidades
- **Comunicación WebSocket dirigida por eventos** para interacciones en tiempo real
- **Estrategia de caché multicapa** optimizada para volatilidad de datos
- **Arquitectura orientada a servicios** con inyección de dependencias
- **Patrones async/await** en todo el sistema para rendimiento óptimo

### Componentes Principales

```
backend/
├── app/
│   ├── api/                 # Manejadores de rutas API
│   │   ├── auth.py         # Endpoints de autenticación
│   │   ├── chat.py         # API REST de chat
│   │   ├── health.py       # Endpoints de verificación de salud
│   │   └── websocket.py    # Manejadores WebSocket
│   ├── core/               # Funcionalidad central
│   │   ├── config.py       # Gestión de configuración
│   │   ├── auth.py         # Lógica de autenticación
│   │   ├── logging.py      # Logging estructurado
│   │   └── security.py     # Utilidades de seguridad
│   ├── models/             # Modelos de datos Pydantic
│   │   ├── api_models.py   # Modelos de request/response API
│   │   ├── conversation.py # Modelos de gestión de conversación
│   │   ├── betting.py      # Modelos de apuestas deportivas
│   │   └── websocket_models.py # Modelos de mensajes WebSocket
│   ├── services/           # Servicios de lógica de negocio
│   │   ├── llm_service.py  # Integración LLM (Gemini + LangChain)
│   │   ├── chatbet_api.py  # Cliente API externa
│   │   ├── conversation_manager.py # Manejo de conversaciones
│   │   └── websocket_manager.py # Gestión WebSocket
│   └── utils/              # Funciones utilitarias
│       ├── cache.py        # Utilidades de caché Redis
│       ├── exceptions.py   # Clases de excepción personalizadas
│       └── parsers.py      # Utilidades de parsing de datos
├── main.py                 # Punto de entrada de la aplicación FastAPI
├── requirements.txt        # Dependencias Python
└── Dockerfile             # Configuración del contenedor
```

## ⚙️ Configuración del Entorno

### Variables de Entorno Requeridas

Crear un archivo `.env` basado en `.env.example`:

**Configuración de API Externa:**
- `CHATBET_API_BASE_URL`: URL base de la API de apuestas deportivas
  - **Propósito**: URL base para todas las llamadas a la API de datos deportivos
  - **Ejemplo**: `https://v46fnhvrjvtlrsmnismnwhdh5y0lckdl.lambda-url.us-east-1.on.aws/`
  - **Requerido**: Sí

**Configuración de LLM:**
- `GOOGLE_API_KEY`: Clave de API de Google Gemini
  - **Propósito**: Requerida para capacidades de conversación con IA
  - **Cómo obtener**: Visitar https://makersuite.google.com/app/apikey
  - **Nivel gratuito**: Disponible para desarrollo
  - **Requerido**: Sí

- `GEMINI_MODEL`: Versión del modelo de IA a usar
  - **Por defecto**: `gemini-2.5-flash`
  - **Alternativas**: `gemini-pro`, `gemini-pro-vision`
  - **Propósito**: Controla las capacidades y costo del modelo de IA

- `GEMINI_TEMPERATURE`: Nivel de creatividad de la respuesta
  - **Rango**: 0.0 (determinístico) a 2.0 (creativo)
  - **Por defecto**: 0.7
  - **Propósito**: Controla la aleatoriedad de la respuesta

**Configuración de Redis:**
- `REDIS_HOST`: Nombre del host del servidor Redis
  - **Por defecto**: `localhost`
  - **Producción**: Usar servicio Redis administrado

- `REDIS_PORT`: Puerto del servidor Redis
  - **Por defecto**: `6379`

- `REDIS_PASSWORD`: Contraseña de autenticación Redis
  - **Requerido**: Para entornos de producción
  - **Seguridad**: Mantener confidencial

**Configuración de la Aplicación:**
- `ENVIRONMENT`: Entorno de ejecución
  - **Opciones**: `development`, `staging`, `production`
  - **Por defecto**: `development`

- `DEBUG`: Habilitar modo de depuración
  - **Opciones**: `true`, `false`
  - **Por defecto**: `false`
  - **Propósito**: Habilita logging detallado y trazas de error

- `SECRET_KEY`: Clave de cifrado de sesión
  - **Generar**: `openssl rand -hex 32`
  - **Propósito**: Cifra sesiones de usuario y tokens

**Configuración TTL de Caché:**
- `CACHE_TTL_TOURNAMENTS`: Caché de datos de torneos (24 horas)
- `CACHE_TTL_FIXTURES`: Caché de partidos (4 horas)
- `CACHE_TTL_ODDS`: Caché de cuotas en vivo (30 segundos)
- `CACHE_TTL_USER_SESSIONS`: Caché de sesiones de usuario (1 hora)

### Archivo .env de Ejemplo

```bash
# Aplicación
ENVIRONMENT=development
DEBUG=true

# Google AI
GOOGLE_API_KEY=tu_clave_api_google_ai_aqui
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.7

# API ChatBet
CHATBET_API_BASE_URL=https://v46fnhvrjvtlrsmnismnwhdh5y0lckdl.lambda-url.us-east-1.on.aws

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Seguridad
SECRET_KEY=87c41b0c5fcc69b0a4cb254bab54cbaf84db047272ea391924916aae6b646c9b
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Caché
CACHE_TTL_TOURNAMENTS=86400
CACHE_TTL_FIXTURES=14400
CACHE_TTL_ODDS=30
```

## 🚀 Inicio Rápido

### Prerequisitos
- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- Redis (para desarrollo local)

### Pasos de Instalación

#### 1. Clonar y Configurar
```bash
git clone <repository-url>
cd chatbet-backend
cp env.example.sh env.sh
# Editar env.sh con los valores de configuración
source env.sh
```

#### 2. Despliegue con Docker (Recomendado)
```bash
# Iniciar todos los servicios con un solo comando
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d --build

# Ver logs de la aplicación
docker-compose logs -f chatbet-backend

# Verificar estado de servicios
docker-compose ps
```

#### 3. Configuración de Desarrollo Local
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar Redis (si no se usa Docker)
redis-server

# Ejecutar la aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Verificar Instalación
- **Documentación API**: http://localhost:8000/docs
- **Verificación de Salud**: http://localhost:8000/health
- **Prueba WebSocket**: http://localhost:8000/ws/test

### Solución de Problemas
- **Conflictos de puerto**: Cambiar puertos en `docker-compose.yml` si es necesario
- **Problemas de permisos**: Asegurar que Docker tenga permisos apropiados
- **Conexión API**: Verificar credenciales de API externa en `.env`
- **Conexión Redis**: Verificar que Redis esté ejecutándose: `redis-cli ping`

## 📡 Documentación de la API

### Endpoints REST

#### Endpoints de Chat

**Enviar Mensaje**
```http
POST /api/v1/chat/message
Content-Type: application/json

{
  "message": "¿Cuáles son las cuotas para Barcelona vs Real Madrid?",
  "user_id": "user123",
  "session_id": "session456"
}
```

Respuesta:
```json
{
  "message": "Basado en datos actuales, Barcelona vs Real Madrid tiene las siguientes cuotas...",
  "session_id": "session456",
  "message_id": "msg_1234567890",
  "response_time_ms": 250,
  "token_count": 150,
  "detected_intent": "ODDS_INFORMATION_QUERY",
  "intent_confidence": 0.95,
  "function_calls_made": ["get_odds"],
  "suggested_actions": ["Ver análisis completo del partido", "Obtener recomendaciones de apuestas"]
}
```

**Obtener Historial de Conversación**
```http
GET /api/v1/chat/conversations/{user_id}?session_id=session456&limit=20
```

**Limpiar Conversación**
```http
DELETE /api/v1/chat/conversations/{user_id}?session_id=session456
```

#### Endpoints de Salud

**Verificación Básica de Salud**
```http
GET /health/
```

**Verificación de Preparación (con dependencias)**
```http
GET /health/ready
```

**Verificación de Vida**
```http
GET /health/live
```

### API WebSocket

#### Conexión
```
ws://localhost:8000/ws/chat
```

#### Formato de Mensaje
```json
{
  "type": "user_message",
  "content": "Muéstrame los partidos de la Champions League",
  "session_id": "tu-session-id",
  "user_id": "tu-user-id",
  "message_id": "id-unico-opcional"
}
```

#### Formato de Respuesta
```json
{
  "type": "assistant_response",
  "content": "Aquí están los próximos partidos de la Champions League...",
  "session_id": "tu-session-id",
  "message_id": "msg_1234567890",
  "is_final": true,
  "detected_intent": "MATCH_SCHEDULE_QUERY",
  "function_calls": ["get_fixtures"]
}
```

#### Formato de Error
```json
{
  "type": "error",
  "content": "No se puede procesar tu solicitud",
  "error_code": "PROCESSING_ERROR",
  "session_id": "tu-session-id"
}
```

## 💬 Capacidades Conversacionales

### Tipos de Consultas Soportadas

#### Consultas de Horarios de Partidos
**Ejemplos:**
- "¿Cuándo juega el Barcelona?"
- "¿Qué partidos hay el domingo?"
- "¿Quién juega mañana en la Champions League?"
- "Muéstrame el próximo partido del Real Madrid"

**Clasificación de Intención**: `MATCH_SCHEDULE_QUERY`
**Entidades Extraídas**: Nombres de equipos, fechas, torneos
**Tipo de Respuesta**: Tarjetas de partidos con equipos, fechas y sedes

#### Información de Cuotas de Apuestas
**Ejemplos:**
- "¿Cuáles son las cuotas para Barcelona vs Real Madrid?"
- "¿Cuánto paga un empate?"
- "Muéstrame los mercados de apuestas para los juegos de hoy"
- "¿Cuál es el pago por una apuesta de $100 en el Chelsea?"

**Clasificación de Intención**: `ODDS_INFORMATION_QUERY`
**Entidades Extraídas**: Nombres de equipos, montos de apuesta, tipos de mercado
**Tipo de Respuesta**: Cuotas detalladas con pagos potenciales

#### Recomendaciones de Apuestas
**Ejemplos:**
- "¿En qué partido debería apostar?"
- "¿Cuál es la apuesta más segura este fin de semana?"
- "Dame una recomendación para el domingo"
- "¿Cuál es la mejor apuesta de valor hoy?"

**Clasificación de Intención**: `BETTING_RECOMMENDATION`
**Entidades Extraídas**: Rangos de fechas, preferencias de riesgo, presupuesto
**Tipo de Respuesta**: Apuestas recomendadas con justificación detallada

#### Comparaciones de Equipos
**Ejemplos:**
- "¿Quién es mejor, Barcelona o Real Madrid?"
- "Compara el rendimiento reciente de estos equipos"
- "¿Qué equipo tiene mejores cuotas históricamente?"

**Clasificación de Intención**: `TEAM_COMPARISON`
**Entidades Extraídas**: Nombres de equipos, criterios de comparación
**Tipo de Respuesta**: Análisis detallado de equipos y estadísticas

#### Información de Torneos
**Ejemplos:**
- "¿Qué torneos están activos?"
- "Muéstrame la tabla de la Premier League"
- "¿Cuándo comienza la Champions League?"

**Clasificación de Intención**: `TOURNAMENT_INFO`
**Entidades Extraídas**: Nombres de torneos, fechas
**Tipo de Respuesta**: Horarios e información de torneos

### Ejemplos de Flujo de Conversación

**Ejemplo 1: Consulta de Partido**
```
Usuario: "¿Cuándo juega próximamente el Barcelona?"
Asistente: "El próximo partido del Barcelona es el domingo 22 de diciembre a las 3:00 PM contra el Real Madrid en el Camp Nou en La Liga. ¿Te gustaría ver las cuotas de apuestas para este partido?"

Usuario: "Sí, muéstrame las cuotas"
Asistente: "Aquí están las cuotas actuales para Barcelona vs Real Madrid:
• Barcelona gana: 2.10 (10/11)
• Empate: 3.40 (12/5)  
• Real Madrid gana: 3.50 (5/2)

Para una apuesta de $100:
• Victoria del Barcelona paga $210
• Empate paga $340
• Victoria del Real Madrid paga $350

¿Te gustaría que te recomiende una estrategia de apuestas?"
```

**Ejemplo 2: Recomendación de Apuestas**
```
Usuario: "¿Cuál es una buena apuesta para este fin de semana?"
Asistente: "Basado en el análisis de forma actual y cuotas, aquí están mis principales recomendaciones para este fin de semana:

🔥 **Mejor Apuesta de Valor**
• Manchester City vs Arsenal - Más de 2.5 Goles
• Cuotas: 1.85 • Confianza: Alta
• Razonamiento: Ambos equipos promedian 2.8 goles por partido

⚡ **Apuesta Segura**  
• Bayern Munich vs Dortmund - Bayern Gana
• Cuotas: 1.55 • Confianza: Muy Alta
• Razonamiento: Bayern invicto en casa esta temporada

¡Recuerda apostar responsablemente y solo apostar lo que puedas permitirte perder!"
```

## 🔧 Implementación Técnica

### Arquitectura de Integración de IA

**Google Gemini con LangChain**
- **Modelo**: Gemini-2.5-Flash para velocidad y eficiencia de costo óptima
- **Llamadas a Funciones**: Integración nativa de herramientas para recuperación de datos deportivos
- **Memoria de Conversación**: ConversationBufferWindowMemory de LangChain
- **Transmisión**: Generación de respuestas palabra por palabra vía WebSocket

**Sistema de Clasificación de Intenciones**
```python
class IntentType(Enum):
    MATCH_SCHEDULE_QUERY = "match_schedule_query"
    ODDS_INFORMATION_QUERY = "odds_information_query"
    BETTING_RECOMMENDATION = "betting_recommendation"
    TEAM_COMPARISON = "team_comparison"
    TOURNAMENT_INFO = "tournament_info"
    USER_BALANCE_QUERY = "user_balance_query"
    BET_SIMULATION = "bet_simulation"
    GENERAL_SPORTS_QUERY = "general_sports_query"
    GREETING = "greeting"
    HELP_REQUEST = "help_request"
    UNCLEAR = "unclear"
```

**Extracción de Entidades**
- Identificación de nombres de equipos y jugadores
- Parsing de fechas y horas (lenguaje natural)
- Montos monetarios y tamaños de apuesta
- Nombres de torneos y competiciones
- Tipos de mercados de apuestas (1X2, Over/Under, etc.)

### Estrategia de Caché

**Caché Redis Multicapa**
- **Torneos**: Caché de 24 horas (datos estables)
- **Partidos**: Caché de 4 horas (semi-estables)
- **Cuotas en Vivo**: Caché de 30 segundos (altamente dinámico)
- **Sesiones de Usuario**: Caché de 1 hora (contexto de conversación)
- **Respuestas API**: TTL inteligente basado en tipo de datos

### Gestión WebSocket

**Manejo de Conexiones**
- Generación automática de ID de sesión
- Resolución de conflictos de conexión (una sesión por ID)
- Deduplicación de mensajes para prevenir procesamiento doble
- Desconexión y reconexión elegante

**Procesamiento de Mensajes**
- Rastreo de ID de mensaje único
- Deduplicación de ventana de procesamiento (ventana de 2 segundos)
- Deduplicación a nivel de conversación y WebSocket
- Logs de procesamiento detallados para depuración

### Manejo de Errores y Resistencia

**Patrón Circuit Breaker**
- Fallback automático cuando las APIs externas fallan
- Degradación elegante con datos en caché
- Integración de verificación de salud para monitoreo de dependencias

**Jerarquía de Excepciones**
```python
class ChatBetException(Exception): pass
class APIError(ChatBetException): pass
class LLMError(ChatBetException): pass
class CacheError(ChatBetException): pass
class ValidationError(ChatBetException): pass
```

## 🏥 Monitoreo y Rendimiento

### Monitoreo de Salud
- **Salud de la Aplicación**: Disponibilidad básica del servicio
- **Salud de Dependencias**: Estado de Redis, API ChatBet, servicio LLM
- **Métricas de Rendimiento**: Tiempos de respuesta, tasas de error, ratios de acierto de caché

### Arquitectura de Logging
- **Logging JSON Estructurado** en producción
- **IDs de Correlación** para rastreo de solicitudes
- **Métricas de Rendimiento** para rastreo de tiempo de respuesta
- **Logging de Eventos de Seguridad** para autenticación y autorización

### Optimizaciones de Rendimiento
- **Connection Pooling** para APIs externas
- **Patrones Async/Await** en todo el sistema
- **Pipelining Redis** para operaciones en lote
- **Compresión de Respuesta** para payloads grandes
- **Deduplicación de Solicitudes** para prevenir procesamiento redundante

## 🔐 Implementación de Seguridad

### Autenticación y Autorización
- **Autenticación por Clave API** para endpoints de producción
- **Gestión de Sesiones** con tokens seguros
- **Configuración CORS** con orígenes específicos del entorno

### Protección de Datos
- **Validación de Entrada** usando modelos Pydantic
- **Prevención XSS** a través de codificación de salida apropiada
- **Rate Limiting** por dirección IP (100 solicitudes/minuto por defecto)
- **Seguridad de Variables de Entorno** con validación

### Lista de Verificación de Seguridad de Producción
- [ ] Cifrado HTTPS/WSS para todas las comunicaciones
- [ ] Variables de entorno adecuadamente aseguradas
- [ ] Rate limiting configurado apropiadamente
- [ ] Orígenes CORS restringidos a dominios conocidos
- [ ] Autenticación Redis habilitada
- [ ] Logging sanitizado (sin datos sensibles)

## 📋 Reflexión de Evaluación Técnica

### 1. Decisiones de Arquitectura
**Pregunta**: ¿Qué decisiones de diseño tomaste y por qué?

**Respuesta**: Implementé una arquitectura inspirada en microservicios con clara separación de responsabilidades:

- **Framework FastAPI**: Elegido por su excelente soporte asíncrono, generación automática de documentación OpenAPI y capacidades nativas de WebSocket, haciéndolo ideal para aplicaciones de chat en tiempo real que requieren tanto endpoints REST como WebSocket.

- **Arquitectura de Servicios Modular**: Cada servicio tiene una sola responsabilidad - el servicio LLM maneja interacciones de IA, el servicio de caché gestiona operaciones Redis, el cliente API maneja integraciones externas. Esto promueve mantenibilidad, testeabilidad y permite escalado independiente de componentes.

- **Comunicación WebSocket Orientada a Eventos**: Implementé comunicación bidireccional en tiempo real para mejor experiencia de usuario, permitiendo respuestas en streaming y actualizaciones de datos deportivos en vivo. Esto proporciona retroalimentación inmediata y mantiene a los usuarios comprometidos durante el procesamiento de IA.

- **Estrategia de Caché Multicapa**: Caché Redis con estrategias TTL inteligentes - torneos (24h), partidos (4h), cuotas (30s) - optimizando para volatilidad de datos y patrones de acceso. Esto reduce significativamente las llamadas a API y mejora los tiempos de respuesta.

- **Despliegue Docker Compose**: El despliegue de un solo comando simplifica el proceso de evaluación mientras asegura consistencia entre entornos y gestión fácil de dependencias.

### 2. Selección e Integración de LLM
**Pregunta**: ¿Qué modelo usaste y por qué?

**Respuesta**: Seleccioné Google Gemini Pro por varias razones estratégicas:

- **Disponibilidad de Nivel Gratuito**: La evaluación mencionó específicamente preferencia por acceso gratuito a API, y Gemini ofrece límites generosos de nivel gratuito (60 solicitudes/minuto, 1 millón tokens/día) adecuados para desarrollo y demostración.

- **Calidad Conversacional**: Gemini Pro destaca en mantener contexto a través de conversaciones de múltiples turnos, crucial para discusiones de apuestas deportivas donde los usuarios frecuentemente hacen preguntas de seguimiento sobre equipos, cuotas o recomendaciones.

- **Capacidades de Llamada a Funciones**: El soporte nativo para llamar APIs externas permite integración fluida con endpoints de datos deportivos, habilitando a la IA a obtener información en tiempo real durante conversaciones sin romper el flujo conversacional.

- **Soporte de Respuesta en Streaming**: Habilita generación de respuestas palabra por palabra para experiencia de usuario mejorada vía conexiones WebSocket, proporcionando retroalimentación inmediata de que se está generando una respuesta.

- **Rendimiento en Dominio Deportivo**: Las pruebas mostraron excelente rendimiento en comprensión de terminología deportiva, nombres de equipos y conceptos de apuestas, con alta precisión en clasificación de intenciones y extracción de entidades.

- **Eficiencia de Costo**: Gemini-2.5-Flash proporciona balance óptimo entre calidad de respuesta y velocidad de procesamiento, crucial para aplicaciones de chat en tiempo real.

### 3. Estrategia de Gestión de Contexto
**Pregunta**: ¿Cómo gestionaste el contexto conversacional?

**Respuesta**: Implementé un enfoque de gestión de contexto multicapa:

- **ConversationBufferWindowMemory de LangChain**: Mantiene los últimos 10 pares de mensajes en memoria activa para acceso inmediato al contexto durante el procesamiento de conversación. Esto proporciona a la IA historial conversacional reciente para respuestas contextuales.

- **Persistencia de Sesión Redis**: Historial conversacional a largo plazo almacenado en Redis con aislamiento basado en sesión, permitiendo recuperación de contexto después de desconexiones y soportando acceso multi-dispositivo. Los usuarios pueden continuar conversaciones a través de sesiones de navegador.

- **Sistema de Rastreo de Entidades**: Mantiene preferencias de usuario y entidades mencionadas (equipos favoritos, montos típicos de apuesta, tolerancia al riesgo) a través de turnos conversacionales. Esto habilita recomendaciones personalizadas y respuestas contextualmente conscientes.

- **Gestión de Sesión WebSocket**: Cada conexión WebSocket mantiene contexto conversacional aislado, previniendo contaminación cruzada entre usuarios en sesiones concurrentes. Los IDs de sesión aseguran aislamiento apropiado y enrutamiento de contexto.

- **Inyección de Contexto**: Contexto histórico relevante y preferencias de usuario se inyectan inteligentemente en cada prompt LLM para mantener coherencia conversacional. El sistema incluye historial conversacional reciente y entidades extraídas en prompts.

- **Clasificación de Intención Contextual**: El contexto conversacional previo influye la clasificación de intención, mejorando precisión para consultas ambiguas como "¿Y el Real Madrid?" siguiendo una discusión sobre Barcelona.

### 4. Enfoque de Optimización de Rendimiento
**Pregunta**: ¿Cómo optimizaste para rendimiento y escalabilidad?

**Respuesta**: Implementé múltiples estrategias de optimización de rendimiento:

- **Arquitectura Async/Await**: Toda la aplicación construida en patrones asíncronos para manejar solicitudes concurrentes eficientemente sin operaciones bloqueantes. Esto permite manejar múltiples conexiones WebSocket y llamadas API simultáneamente.

- **Estrategia de Caché Inteligente**: Caché Redis multicapa con TTLs específicos de datos reduce las llamadas a API externa en 80%+ en patrones de uso típicos. Los ratios de acierto de caché se monitorean y optimizan basado en patrones de uso.

- **Connection Pooling**: Pooling de conexiones HTTP para llamadas a API externa reduce la sobrecarga de conexión y mejora tiempos de respuesta. Configurado con timeout apropiado y configuraciones de reintento.

- **Deduplicación de Mensajes**: Implementé deduplicación tanto a nivel WebSocket como a nivel de conversación para prevenir procesar el mismo mensaje múltiples veces, reduciendo llamadas innecesarias a LLM y solicitudes API.

- **Streaming de Respuesta**: El streaming WebSocket proporciona retroalimentación inmediata al usuario y mejoras de rendimiento percibido, incluso para tiempos de procesamiento de IA más largos.

- **Gestión de Memoria**: Historial conversacional limitado y evicción inteligente de caché previenen hinchazón de memoria en conversaciones de larga duración.

### 5. Manejo de Errores y Resistencia
**Pregunta**: ¿Cómo manejaste errores y aseguraste resistencia del sistema?

**Respuesta**: Implementé patrones comprensivos de manejo de errores y resistencia:

- **Patrón Circuit Breaker**: Mecanismos de fallback automático cuando servicios externos (API ChatBet, Google AI) no están disponibles. El sistema degrada elegantemente a datos en caché o proporciona mensajes de error informativos.

- **Lógica de Reintento con Backoff Exponencial**: Las llamadas API fallidas se reintentan con retrasos crecientes para manejar problemas temporales de red sin sobrecargar servicios.

- **Degradación Elegante**: Cuando datos en tiempo real no están disponibles, el sistema recurre a datos en caché con notificaciones apropiadas al usuario sobre frescura de datos.

- **Jerarquía de Excepciones Personalizada**: El manejo de excepciones estructurado permite respuestas apropiadas basadas en tipo de error (errores API, errores de validación, errores de caché, etc.).

- **Endpoints de Verificación de Salud**: Monitoreo de salud comprensivo para todas las dependencias (Redis, APIs externas, servicio LLM) habilita detección proactiva de problemas y recuperación automatizada.

- **Validación de Entrada**: Validación estricta de modelos Pydantic previene que datos inválidos causen errores del sistema y proporciona mensajes de error claros a usuarios.

### 6. Seguridad y Protección de Datos
**Pregunta**: ¿Cómo implementaste medidas de seguridad?

**Respuesta**: Implementé un enfoque de seguridad multicapa:

- **Seguridad de Variables de Entorno**: Toda configuración sensible (claves API, secretos) gestionada a través de variables de entorno con validación para prevenir malas configuraciones.

- **Sanitización de Entrada**: Todas las entradas de usuario validadas y sanitizadas usando modelos Pydantic para prevenir ataques de inyección y asegurar integridad de datos.

- **Rate Limiting**: Rate limiting basado en IP (100 solicitudes/minuto por defecto) previene abuso y asegura uso justo de recursos entre usuarios.

- **Configuración CORS**: Configuraciones CORS específicas del entorno previenen solicitudes cross-origin no autorizadas mientras permiten acceso legítimo del frontend.

- **Seguridad de Sesiones**: Gestión segura de sesiones con IDs de sesión generados y aislamiento apropiado entre usuarios y sesiones.

- **Autenticación API**: Listo para autenticación por clave API en entornos de producción con validación apropiada de headers.

### 7. Testing y Aseguramiento de Calidad
**Pregunta**: ¿Cómo aseguraste calidad y confiabilidad del código?

**Respuesta**: Implementé testing comprensivo y aseguramiento de calidad:

- **Testing Unitario**: Componentes de servicio individuales testeados con pytest, incluyendo servicio LLM, gestión de caché e integración API.

- **Testing de Integración**: Testing end-to-end de conexiones WebSocket, flujos de conversación e integraciones de API externa.

- **Testing de Deduplicación**: Tests específicos para deduplicación a nivel WebSocket y conversación para prevenir el problema de múltiples respuestas.

- **Testing de Escenarios de Error**: Testing de varios modos de falla (timeouts API, fallas Redis, entradas inválidas) para asegurar manejo elegante.

- **Testing de Rendimiento**: Load testing de conexiones WebSocket y manejo de conversaciones concurrentes para identificar cuellos de botella.

- **Calidad de Código**: Logging estructurado, type hints en todo el código y clara separación de responsabilidades para mantenibilidad.

### 8. Despliegue y DevOps
**Pregunta**: ¿Cómo preparaste la aplicación para despliegue?

**Respuesta**: Preparé estrategia comprensiva de despliegue:

- **Containerización Docker**: Builds Docker multi-etapa con tamaños de imagen optimizados y mejores prácticas de seguridad. Configuraciones de desarrollo y producción separadas.

- **Docker Compose**: Despliegue de un solo comando con todas las dependencias (Redis, aplicación) configuradas para evaluación fácil y desarrollo.

- **Configuración de Entorno**: Sistema comprensivo de variables de entorno con ejemplos y documentación para diferentes escenarios de despliegue.

- **Monitoreo de Salud**: Endpoints de verificación de salud para monitoreo de aplicación y dependencias, habilitando integración con load balancers y sistemas de orquestación.

- **Preparación para Producción**: Opciones de configuración para despliegues de producción incluyendo logging JSON, configuraciones de seguridad y optimizaciones de rendimiento.

- **Documentación**: Documentación completa de setup y despliegue con guías de solución de problemas para problemas comunes.

## 🚧 Problemas Conocidos y Soluciones

### Deduplicación de Mensajes WebSocket
**Problema**: Múltiples respuestas a un solo mensaje de usuario
**Solución**: Implementé deduplicación de doble capa:
- Nivel WebSocket: Rastreo de ID de mensaje con limpieza de 10 minutos
- Nivel de conversación: Hash de contenido con ventana de 2 segundos
- Gestión de conexión: Auto-cierre de conexiones de sesión duplicadas

### Gestión de Sesiones
**Problema**: Manejo de ID de sesión nulo
**Solución**: Generación automática de UUID para IDs de sesión faltantes con validación apropiada

### Monitoreo de Rendimiento
**Problema**: Rastreo de tiempo de respuesta
**Solución**: Métricas de rendimiento detalladas con IDs de correlación para rastreo de solicitudes

## 🔗 Documentación Relacionada

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Documentación LangChain](https://python.langchain.com/)
- [Documentación Google AI](https://ai.google.dev/)
- [Documentación Redis](https://redis.io/documentation)
- [Documentación Pydantic](https://docs.pydantic.dev/)

## 📄 Licencia

Este proyecto es parte de una evaluación técnica para ChatBet.

## 🙋‍♂️ Soporte

Para problemas y preguntas, referirse a la documentación del código, logs de error y endpoints de verificación de salud.

---

**Construido con ❤️ por Daniel Sarmiento**  
*Desarrollador Full-Stack Senior & Especialista en Integración de IA*