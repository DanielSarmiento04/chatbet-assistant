# ChatBet Assistant - Plataforma Conversacional de IA para Apuestas Deportivas

## 🎯 Descripción del Proyecto

**ChatBet Assistant** es una plataforma conversacional de IA comprensiva diseñada para información de apuestas deportivas, comparación de cuotas en tiempo real y recomendaciones de apuestas personalizadas. Construida con tecnologías modernas incluyendo backend FastAPI con integración de Google Gemini AI y frontend Angular 19 con Material Design 3.

**Características Principales:**
- 🤖 **Conversación Inteligente**: Interacción en lenguaje natural con Google Gemini 2.5-Flash AI
- ⚡ **Datos en Tiempo Real**: Transmisión de datos deportivos en vivo vía WebSocket
- 🎨 **UI Moderna**: Angular 19 con gestión de estado basada en signals y Material Design 3
- 🔐 **Arquitectura Segura**: Autenticación JWT con gestión de sesiones Redis
- 🐳 **Despliegue Containerizado**: Soporte completo de Docker con orquestación
- 🌐 **Soporte Bilingüe**: Documentación completa en inglés y español
- 📱 **Diseño Responsivo**: Enfoque mobile-first con capacidades PWA

## 🎬 Demo

¡Mira ChatBet Assistant en acción! La demostración muestra la experiencia completa de IA conversacional incluyendo interacción de chat en tiempo real, transmisión de datos deportivos y recomendaciones inteligentes de apuestas.

**Video de Demostración**: `output_o.mp4`

<video width="320" height="240" controls>
  <source src="output_o.mp4" type="video/mp4">
</video>

La demostración incluye:
- 💬 **Chat en Lenguaje Natural**: Conversación fluida con el asistente de IA
- 🏈 **Consultas de Datos Deportivos**: Información deportiva y estadísticas en tiempo real
- 📊 **Visualización de Cuotas**: Comparación y análisis de cuotas en vivo
- ⚡ **Comunicación WebSocket**: Entrega instantánea de mensajes y respuestas
- 📱 **Interfaz Responsiva**: Experiencia móvil y de escritorio
- 🎯 **Recomendaciones de IA**: Sugerencias inteligentes de apuestas basadas en consultas del usuario

## 🏗️ Descripción de la Arquitectura

### Arquitectura del Sistema
```
┌─────────────────────────────────────────────────────────────┐
│                   Plataforma ChatBet                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Angular 19)          │  Backend (FastAPI)        │
│  ├── Gestión Estado Signals     │  ├── Google Gemini AI     │
│  ├── UI Material Design 3       │  ├── Caché Redis          │
│  ├── Cliente WebSocket          │  ├── Autenticación JWT    │
│  ├── Capacidades PWA            │  ├── Streaming API Sports │
│  └── Diseño Responsivo          │  └── Servidor WebSocket   │
├─────────────────────────────────────────────────────────────┤
│                  Infraestructura                           │
│  ├── Contenedores Docker        │  ├── Aislamiento Red      │
│  ├── Base Datos Redis           │  ├── Config Entorno       │
│  └── Orquestación Multi-servicio│  └── Monitoreo Salud      │
└─────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

**Backend:**
- **Framework**: FastAPI (Python 3.11+)
- **Motor IA**: Google Gemini 2.5-Flash con LangChain
- **Base de Datos**: Redis para caché y sesiones
- **Comunicación**: WebSocket para actualizaciones en tiempo real
- **Autenticación**: JWT con gestión segura de tokens
- **Containerización**: Docker con builds multi-etapa

**Frontend:**
- **Framework**: Angular 19 con componentes standalone
- **Gestión Estado**: Angular Signals + patrones RxJS
- **Librería UI**: Angular Material 19 con Material Design 3
- **Tiempo Real**: Cliente Socket.IO para comunicación WebSocket
- **Lenguaje**: TypeScript 5.6+ con verificación de tipos estricta
- **Sistema Build**: Angular CLI con optimización esbuild

**Infraestructura:**
- **Orquestación**: Docker Compose con networking de servicios
- **Caché**: Redis con invalidación basada en TTL
- **Despliegue**: Soporte de configuración multi-entorno
- **Monitoreo**: Health checks e integración de logging

## 🚀 Inicio Rápido

### Prerequisitos
- **Docker & Docker Compose**: Versiones más recientes
- **Node.js**: 18.19+ o 20.9+ (para desarrollo frontend)
- **Python**: 3.11+ (para desarrollo backend)
- **Git**: Para control de versiones

### Opción 1: Despliegue Docker (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd chatbet-assistant

# Iniciar todos los servicios
docker-compose up -d

# Acceder a la aplicación
# Frontend: http://localhost:4200
# Backend API: http://localhost:8000
# Documentación API: http://localhost:8000/docs
```

### Opción 2: Configuración de Desarrollo

#### Configuración Backend
```bash
cd chatbet-backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Configurar entorno
cp backend/env.example.sh backend/env.sh
# Editar env.sh con tu configuración

# Iniciar servidor de desarrollo
source backend/env.sh
python backend/main.py
```

#### Configuración Frontend
```bash
cd chatbet-frontend

# Instalar dependencias (recomendado: usar bun para instalaciones más rápidas)
bun install
# o npm install

# Iniciar servidor de desarrollo
bun run start
# o ng serve

# Acceder en http://localhost:4200
```

### Configuración de Entorno

Crear archivos de entorno basados en tu configuración:

**Entorno Backend** (`chatbet-backend/backend/env.sh`):
```bash
export GEMINI_API_KEY="tu-clave-api-gemini"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET_KEY="tu-clave-secreta-jwt-segura"
export CORS_ORIGINS="http://localhost:4200"
export LOG_LEVEL="INFO"
```

**Entorno Frontend** (`chatbet-frontend/src/environments/environment.ts`):
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000/ws/chat',
  enableLogging: true
};
```

## 📁 Estructura del Proyecto

```
chatbet-assistant/
├── README.md                    # Este archivo - descripción del proyecto
├── README_ES.md                 # Versión en español de la descripción del proyecto
├── docker-compose.yml           # Orquestación multi-servicio
├── chatbet-backend/            # Servicio backend FastAPI
│   ├── README.md               # Documentación específica del backend
│   ├── README_ES.md            # Documentación backend en español
│   ├── docker-compose.yml      # Configuración servicio backend
│   └── backend/                # Código aplicación Python
│       ├── main.py             # Punto entrada aplicación FastAPI
│       ├── requirements.txt    # Dependencias Python
│       ├── app/                # Módulos de aplicación
│       │   ├── api/            # Definiciones rutas API
│       │   ├── core/           # Funcionalidad central (auth, config)
│       │   ├── models/         # Modelos datos y esquemas
│       │   ├── services/       # Servicios lógica negocio
│       │   └── utils/          # Funciones utilidad
│       └── tests/              # Suite de pruebas
└── chatbet-frontend/           # Aplicación frontend Angular
    ├── README.md               # Documentación específica del frontend
    ├── README_ES.md            # Documentación frontend en español
    ├── docker-compose.yml      # Configuración servicio frontend
    ├── angular.json            # Configuración Angular CLI
    ├── package.json            # Dependencias Node.js
    └── src/                    # Código fuente aplicación Angular
        ├── app/                # Componentes y servicios aplicación
        │   ├── components/     # Componentes UI reutilizables
        │   ├── pages/          # Componentes página basados en rutas
        │   ├── services/       # Servicios Angular
        │   └── models/         # Definiciones tipos TypeScript
        └── environments/       # Configuraciones entorno
```

## 🔧 Flujo de Desarrollo

### Desarrollo Backend
```bash
cd chatbet-backend

# Configurar entorno de desarrollo
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Ejecutar pruebas
python -m pytest backend/test_*.py

# Iniciar servidor desarrollo con hot reload
python backend/main.py

# Documentación API disponible en http://localhost:8000/docs
```

### Desarrollo Frontend
```bash
cd chatbet-frontend

# Instalar dependencias
bun install

# Iniciar servidor de desarrollo
bun run start

# Ejecutar pruebas
bun run test

# Build para producción
bun run build:prod

# Lint de código
bun run lint
```

### Desarrollo Docker
```bash
# Construir e iniciar todos los servicios
docker-compose up --build

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir servicio específico
docker-compose up --build chatbet-backend
```

## 🌐 Documentación API

### Endpoints Principales

**Health Check:**
```bash
GET /api/v1/health
# Respuesta: {"status": "healthy", "timestamp": "2025-09-19T10:00:00Z"}
```

**Autenticación:**
```bash
POST /api/v1/auth/login
# Body: {"username": "usuario", "password": "contraseña"}
# Respuesta: {"access_token": "jwt-token", "token_type": "bearer"}
```

**Conversación Chat:**
```bash
POST /api/v1/chat/message
# Headers: Authorization: Bearer <token>
# Body: {"message": "¿Cuáles son los partidos de fútbol de hoy?", "session_id": "uuid"}
```

**Conexión WebSocket:**
```javascript
// Conectar a WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat');

// Enviar mensaje
ws.send(JSON.stringify({
  type: 'message',
  data: {
    content: 'Muéstrame las cuotas de apuestas para Lakers vs Warriors',
    session_id: 'session-uuid'
  }
}));
```

### Documentación Interactiva API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Características de Seguridad

### Seguridad Backend
- **Autenticación JWT**: Autenticación segura basada en tokens
- **Protección CORS**: Intercambio de recursos de origen cruzado configurable
- **Validación Entrada**: Validación modelo Pydantic para todas las entradas
- **Limitación Tasa**: Protección contra abuso API
- **Headers Seguros**: Headers de seguridad para todas las respuestas

### Seguridad Frontend
- **Protección XSS**: Sanitización entrada y renderizado seguro
- **Protección CSRF**: Validación solicitud basada en token
- **Almacenamiento Seguro**: Gestión y almacenamiento seguro de tokens
- **Política Seguridad Contenido**: Headers CSP estrictos
- **Aplicación HTTPS**: Comunicación segura en producción

## 📊 Rendimiento y Monitoreo

### Métricas de Rendimiento
- **Tiempo Respuesta Backend**: < 200ms para llamadas API
- **Latencia WebSocket**: < 50ms para mensajes tiempo real
- **Tiempo Carga Frontend**: < 1.5s carga inicial página
- **Tamaño Bundle**: < 2MB build producción optimizado

### Monitoreo y Logging
```bash
# Ver logs aplicación
docker-compose logs -f chatbet-backend
docker-compose logs -f chatbet-frontend

# Monitorear rendimiento Redis
docker-compose exec redis redis-cli monitor

# Endpoints health check
curl http://localhost:8000/api/v1/health
curl http://localhost:4200/health
```

## 🚧 Solución de Problemas

### Problemas Comunes

**Backend No Inicia:**
```bash
# Verificar variables de entorno
source backend/env.sh
echo $GEMINI_API_KEY

# Verificar conexión Redis
docker-compose exec redis redis-cli ping

# Verificar disponibilidad puerto
lsof -i :8000
```

**Falla Build Frontend:**
```bash
# Limpiar caché y reinstalar
rm -rf node_modules bun.lockb
bun install

# Verificar versión Angular CLI
ng version

# Verificar compilación TypeScript
npx tsc --noEmit
```

**Problemas Conexión WebSocket:**
```bash
# Probar endpoint WebSocket
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/chat
```

**Problemas Docker:**
```bash
# Reconstruir todos los servicios
docker-compose down -v
docker-compose up --build

# Verificar estado servicios
docker-compose ps

# Ver logs detallados
docker-compose logs --details chatbet-backend
```

## 🌍 Internacionalización

Este proyecto proporciona documentación bilingüe completa:

### Documentación en Inglés
- `README.md` - Descripción global proyecto (este archivo)
- `chatbet-backend/README.md` - Documentación técnica backend
- `chatbet-frontend/README.md` - Documentación técnica frontend

### Documentación en Español
- `README_ES.md` - Descripción global proyecto en español
- `chatbet-backend/README_ES.md` - Documentación backend en español
- `chatbet-frontend/README_ES.md` - Documentación frontend en español

Toda la documentación mantiene paridad de características entre idiomas con terminología técnica apropiada y localización cultural.


### Documentación
- Backend API: http://localhost:8000/docs
- Componentes Frontend: Referirse a documentación Angular
- Configuración Docker: Ver configuración docker-compose.yml

### Recursos de Desarrollo
- **Angular 19**: https://angular.dev/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Google Gemini**: https://ai.google.dev/
- **Redis**: https://redis.io/documentation
- **Material Design 3**: https://material.angular.io/

### Solución de Problemas
- Verificar logs servicios: `docker-compose logs -f`
- Verificar configuración entorno
- Asegurar que todos los prerequisitos estén instalados
- Revisar conectividad red entre servicios

---

**Construido con ❤️ por Daniel Sarmiento**  
*Desarrollador Full-Stack Senior y Especialista en Integración de IA*

**Estado del Proyecto**: Desarrollo Activo  
**Versión**: 1.0.0  
**Última Actualización**: 19 de septiembre, 2025