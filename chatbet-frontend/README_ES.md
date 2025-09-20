# ChatBet Frontend - Interfaz Conversacional de IA para Apuestas Deportivas

## 🎯 Descripción del Proyecto

Aplicación frontend moderna de Angular 19 que proporciona una interfaz conversacional inteligente para información de apuestas deportivas, comparación de cuotas en tiempo real y recomendaciones de apuestas personalizadas. Construida con las características más avanzadas de Angular 19, incluyendo signals, componentes standalone y experiencia de desarrollador mejorada.

**Características Principales:**
- Interfaz de chat conversacional con IA en tiempo real
- Transmisión de datos deportivos en vivo impulsada por WebSocket
- Gestión de estado moderna basada en signals de Angular 19
- Componentes UI responsivos con Material Design 3 (MDC)
- Comparación de cuotas e información de apuestas en tiempo real
- Capacidades de Progressive Web App (PWA)
- Desarrollo TypeScript-first con seguridad de tipos estricta
- Diseño compatible con accesibilidad (WCAG 2.1 AA)

## 🏗️ Arquitectura Técnica

### Stack Tecnológico
- **Framework**: Angular 19 con componentes standalone
- **Gestión de Estado**: Angular Signals + patrones reactivos RxJS
- **Librería UI**: Angular Material 19 con Material Design 3
- **Comunicación en Tiempo Real**: WebSocket + cliente Socket.IO
- **Sistema de Build**: Angular CLI con optimización esbuild
- **Lenguaje**: TypeScript 5.6+ con verificación de tipos estricta
- **Estilos**: SCSS con propiedades CSS personalizadas
- **Testing**: Jasmine + Karma + Angular Testing Library

### Características Modernas de Angular 19
- **Componentes Standalone**: Sin NgModules, arquitectura de componentes simplificada
- **Signals**: Gestión de estado reactiva con optimización automática de detección de cambios
- **Material Design 3**: Sistema de diseño más reciente con temas dinámicos
- **DX Mejorado**: Experiencia de desarrollador mejorada con mejores herramientas de debugging
- **esbuild**: Builds más rápidos y hot module replacement
- **Inyectores Opcionales**: Patrones de inyección de dependencias mejorados

### Estructura del Proyecto

```
src/
├── app/
│   ├── components/           # Componentes UI reutilizables
│   │   ├── chat-interface/   # Componente principal de conversación
│   │   ├── chat-input/       # Entrada de mensaje con indicadores de escritura
│   │   ├── message-bubble/   # Visualización de mensaje individual
│   │   ├── header/           # Encabezado de aplicación con navegación
│   │   └── sidebar/          # Navegación y controles de usuario
│   ├── pages/               # Componentes de página basados en rutas
│   │   ├── chat/            # Página principal de chat
│   │   ├── dashboard/       # Dashboard deportivo
│   │   ├── profile/         # Gestión de perfil de usuario
│   │   └── login/           # Páginas de autenticación
│   ├── services/            # Servicios de lógica de negocio central
│   │   ├── chat.service.ts  # Gestión de conversación de chat
│   │   ├── websocket.service.ts # Comunicación en tiempo real
│   │   ├── auth.service.ts  # Autenticación y autorización
│   │   ├── api.service.ts   # Cliente API HTTP
│   │   └── sports.service.ts # Gestión de datos deportivos
│   ├── models/              # Definiciones de tipos TypeScript
│   │   ├── chat.models.ts   # Tipos de chat y conversación
│   │   ├── sports.models.ts # Interfaces de datos deportivos
│   │   ├── user.models.ts   # Tipos de usuario y autenticación
│   │   └── api.models.ts    # Tipos de request/response API
│   ├── utils/               # Funciones utilitarias y helpers
│   │   ├── common.utils.ts  # Utilidades de propósito general
│   │   ├── sports.utils.ts  # Formateo de datos deportivos
│   │   └── chat.utils.ts    # Procesamiento de mensajes de chat
│   ├── app.component.ts     # Componente raíz de aplicación
│   ├── app.config.ts        # Configuración de aplicación
│   └── app.routes.ts        # Definiciones de rutas
├── environments/            # Configuraciones de entorno
├── styles.scss              # Estilos globales y theming
└── main.ts                  # Bootstrap de aplicación
```

## 🚀 Comenzando

### Prerequisitos
- **Node.js**: 18.19+ o 20.9+ (LTS recomendado)
- **npm**: 9+ o **bun**: 1.0+ (para gestión de paquetes más rápida)
- **Angular CLI**: 19+ (`npm install -g @angular/cli`)
- **Git**: Para control de versiones

### Pasos de Instalación

#### 1. Clonar y Configurar
```bash
# Clonar el repositorio
git clone <repository-url>
cd chatbet-frontend

# Instalar dependencias (recomendado: usar bun para instalaciones más rápidas)
bun install
# o npm install

# Verificar versión de Angular CLI
ng version
```

#### 2. Configuración de Entorno

Crear archivos de entorno basados en tu configuración:

**Entorno de Desarrollo** (`src/environments/environment.ts`):
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000/ws/chat',
  enableLogging: true,
  features: {
    voiceInput: true,
    darkMode: true,
    realTimeUpdates: true,
    pushNotifications: false
  }
};
```

**Entorno de Producción** (`src/environments/environment.prod.ts`):
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://your-production-api.com',
  wsUrl: 'wss://your-production-api.com/ws/chat',
  enableLogging: false,
  features: {
    voiceInput: true,
    darkMode: true,
    realTimeUpdates: true,
    pushNotifications: true
  }
};
```

#### 3. Configuración del Backend

Asegúrate de que el backend de ChatBet esté ejecutándose localmente:
```bash
# En el directorio chatbet-backend
docker-compose up -d
# o
python main.py
```

El frontend espera que el backend esté disponible en:
- **API**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8000/ws/chat`

#### 4. Servidor de Desarrollo

Iniciar el servidor de desarrollo con hot reload:
```bash
# Iniciar servidor de desarrollo
ng serve
# o con bun
bun run start

# Abrir navegador en http://localhost:4200
```

#### 5. Build para Producción

Crear build optimizado de producción:
```bash
# Build de producción
ng build --configuration production
# o
bun run build:prod

# Los artefactos de build estarán en dist/chatbet-frontend/
```

### Comandos de Desarrollo

```bash
# Servidor de desarrollo con live reload
ng serve --open

# Ejecutar pruebas
ng test

# Ejecutar pruebas e2e
ng e2e

# Lint del código
ng lint

# Generar componente
ng generate component components/my-component --standalone

# Generar servicio
ng generate service services/my-service

# Analizar tamaño del bundle
ng build --stats-json
npx webpack-bundle-analyzer dist/chatbet-frontend/stats.json
```

## 📋 Reflexión de Evaluación Técnica

### 1. Implementación de Características de Angular 19
**Pregunta**: ¿Cómo aprovechaste las nuevas características de Angular 19?

**Respuesta**: Implementé una aplicación Angular 19 comprensiva utilizando las últimas capacidades del framework:

- **Componentes Standalone**: Eliminé NgModules completamente, usando componentes standalone en toda la aplicación para arquitectura simplificada y mejor tree-shaking. Cada componente importa solo lo que necesita directamente.

- **Signals para Gestión de Estado**: Reemplacé la gestión de estado reactiva tradicional con Angular Signals, proporcionando reactividad granular y optimización automática de detección de cambios. Implementé signals para todo el estado de servicios incluyendo mensajes, estado de conexión y autenticación de usuario.

- **Integración Material Design 3**: Utilicé Angular Material 19 con componentes Material Design 3 (MDC), proporcionando sistema de diseño moderno con temas dinámicos y accesibilidad mejorada.

- **DX Mejorado**: Aproveché la integración TypeScript mejorada, mejores herramientas de debugging y esbuild para builds de desarrollo más rápidos y hot module replacement.

- **Sintaxis de Control Flow**: Usé la nueva sintaxis de control flow `@if`, `@for` y `@switch` para mejor rendimiento de templates y experiencia de desarrollador.

### 2. Arquitectura de Comunicación en Tiempo Real
**Pregunta**: ¿Cómo implementaste la comunicación WebSocket?

**Respuesta**: Implementé comunicación robusta en tiempo real usando WebSocket con manejo comprensivo de errores:

- **Integración Socket.IO**: Usé cliente Socket.IO para comunicación WebSocket confiable con reconexión automática, monitoreo de heartbeat y soporte de transporte de fallback.

- **Streams Reactivos**: Combiné eventos WebSocket con observables RxJS y signals de Angular para actualizaciones de estado en tiempo real sin interrupciones. Los mensajes fluyen a través de streams reactivos que actualizan automáticamente los componentes UI.

- **Gestión de Conexión**: Implementé monitoreo de estado de conexión, reconexión automática con backoff exponencial, y cola de mensajes durante desconexiones para asegurar que no se pierdan datos.

- **Seguridad de Tipos**: Definí interfaces TypeScript comprensivas para todos los mensajes WebSocket, asegurando seguridad de tipos a través de la comunicación en tiempo real.

### 3. Estrategia de Gestión de Estado
**Pregunta**: ¿Cómo manejaste la gestión de estado compleja?

**Respuesta**: Diseñé un enfoque híbrido de gestión de estado combinando Angular Signals con RxJS:

- **Arquitectura Signals-First**: Usé signals para gestión de estado síncrono (mensajes, estado de usuario, estado UI) con optimización automática de detección de cambios y valores computados para estado derivado.

- **RxJS para Operaciones Async**: Mantuve observables RxJS para operaciones asíncronas como eventos WebSocket, solicitudes HTTP y transformaciones de datos complejas.

- **Estado Centrado en Servicios**: Centralicé la gestión de estado en servicios Angular con clara separación de responsabilidades - ChatService para estado de conversación, WebSocketService para comunicación en tiempo real, AuthService para gestión de usuario.

- **Valores Computados**: Aproveché signals computados para estado derivado como conteos de mensajes, indicadores de escritura y cálculos de estado UI, asegurando actualizaciones automáticas sin gestión manual de suscripciones.

### 4. Técnicas de Optimización de Rendimiento
**Pregunta**: ¿Qué optimizaciones de rendimiento implementaste?

**Respuesta**: Apliqué múltiples estrategias de optimización de rendimiento:

- **Optimización de Bundle**: Configuré Angular CLI con tree-shaking, división de código y presupuestos de bundle. Implementé lazy loading para rutas y componentes para reducir el tamaño inicial del bundle.

- **Optimización de Detección de Cambios**: Usé estrategia OnPush de detección de cambios donde fue apropiado y aproveché signals para optimización automática de detección de cambios.

- **Virtual Scrolling**: Implementé virtual scrolling de CDK para listas grandes de mensajes para mantener rendimiento suave con miles de mensajes.

- **Gestión de Memoria**: Limpieza apropiada de suscripciones usando el operador takeUntilDestroyed y limpieza de efectos en componentes basados en signals.

- **Estrategia de Caché**: Implementé caché inteligente para datos deportivos con invalidación basada en TTL y actualizaciones optimistas para mejor rendimiento percibido.

### 5. Diseño de Arquitectura de Componentes
**Pregunta**: ¿Cómo estructuraste tu arquitectura de componentes?

**Respuesta**: Diseñé una arquitectura de componentes escalable usando mejores prácticas de Angular 19:

- **Componentes Standalone**: Cada componente es standalone con importaciones explícitas, mejorando tree-shaking y reduciendo tamaño de bundle.

- **Patrón Smart/Dumb Component**: Clara separación entre componentes contenedor (páginas) que gestionan estado y componentes de presentación (elementos UI) que reciben datos via inputs.

- **Composición sobre Herencia**: Construí UI compleja a través de composición de componentes en lugar de herencia, usando Angular CDK para composición de comportamiento.

- **Sistema de Diseño Reutilizable**: Creé un sistema de diseño consistente con componentes reutilizables que siguen principios de Material Design 3 y mantienen espaciado consistente, tipografía y patrones de interacción.

### 6. Integración TypeScript y Seguridad de Tipos
**Pregunta**: ¿Cómo aseguraste la seguridad de tipos en toda la aplicación?

**Respuesta**: Implementé integración TypeScript comprensiva con verificación de tipos estricta:

- **Configuración Modo Estricto**: Habilité todas las opciones estrictas del compilador TypeScript incluyendo verificaciones null estrictas, no implicit any, y tipos de función estrictos.

- **Tipos de Modelo de Dominio**: Definí definiciones de tipos comprensivas para todos los modelos de dominio (ChatMessage, User, BettingOdds, etc.) con herencia y composición apropiadas.

- **Patrones de Tipos Genéricos**: Usé genéricos TypeScript para métodos de servicio API reutilizables e interfaces de componentes, asegurando seguridad de tipos a través de diferentes tipos de datos.

- **Verificación de Tipos de Template**: Habilité verificación estricta de tipos de template en Angular para capturar errores de template en tiempo de compilación.

### 7. Implementación de Estrategia de Testing
**Pregunta**: ¿Cómo abordaste el testing en Angular 19?

**Respuesta**: Implementé estrategia de testing comprensiva usando prácticas modernas de testing de Angular:

- **Angular Testing Library**: Usé Angular Testing Library para testing de componentes con enfoques centrados en el usuario, enfocándome en testing de comportamiento en lugar de detalles de implementación.

- **Testing de Signals**: Desarrollé patrones para testing de gestión de estado basada en signals, asegurando que valores computados y efectos funcionen correctamente.

- **Testing de Servicios**: Pruebas unitarias comprensivas para todos los servicios usando TestBed con inyección de dependencias apropiada y estrategias de mocking.

- **Testing E2E**: Implementé pruebas Cypress para flujos críticos de usuario, incluyendo testing de comunicación WebSocket y validación de escenarios de error.

### 8. Implementación de Accesibilidad y UX
**Pregunta**: ¿Cómo aseguraste accesibilidad y buena experiencia de usuario?

**Respuesta**: Prioricé accesibilidad y UX en todo el diseño de la aplicación:

- **Cumplimiento WCAG 2.1 AA**: Implementé HTML semántico, etiquetas ARIA apropiadas, soporte de navegación por teclado y cumplimiento de contraste de color.

- **Material Design 3**: Aproveché componentes Angular Material que proporcionan soporte de accesibilidad incorporado con gestión apropiada de foco y compatibilidad con lectores de pantalla.

- **Mejora Progresiva**: Diseñé la aplicación para funcionar sin JavaScript, con funcionalidad mejorada cuando esté disponible.

- **Diseño Responsivo**: Implementé diseño responsivo mobile-first con targets de toque apropiados y layouts optimizados para todos los tamaños de dispositivo.

- **Estados de Carga**: Estados de carga comprensivos, límites de error y retroalimentación de usuario para todas las operaciones asíncronas para mantener buen rendimiento percibido.

## 🚧 Problemas Conocidos y Soluciones

### Gestión de Conexión WebSocket
**Problema**: Las conexiones se caen durante cambios de red o suspensión del navegador
**Solución**: Implementé reconexión con backoff exponencial y cola de mensajes
**Configuración**:
```typescript
websocket: {
  reconnectInterval: 5000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  connectionTimeout: 10000
}
```

### Optimización de Tamaño de Bundle
**Problema**: Tamaño inicial de bundle grande con componentes Material Design
**Solución**: Implementé importaciones selectivas y lazy loading
**Ejemplo**:
```typescript
// En lugar de importar módulo Material completo
import { MatButtonModule } from '@angular/material/button';
// Solo importar componentes específicos necesarios
```

### Memory Leaks en Sesiones Largas
**Problema**: Los efectos de signals y observables pueden causar memory leaks
**Solución**: Limpieza apropiada usando takeUntilDestroyed y limpieza de efectos
**Patrón**:
```typescript
constructor() {
  effect(() => {
    // Lógica del efecto
  }, { allowSignalWrites: true });
}

ngOnDestroy() {
  // Limpieza automática con takeUntilDestroyed
}
```

## 🔗 Documentación Relacionada

- [Documentación Angular 19](https://angular.dev/)
- [Documentación Angular Material](https://material.angular.io/)
- [Guía Angular Signals](https://angular.dev/guide/signals)
- [Documentación Cliente Socket.IO](https://socket.io/docs/v4/client-api/)
- [Manual TypeScript](https://www.typescriptlang.org/docs/)
- [Angular Testing Library](https://testing-library.com/docs/angular-testing-library/intro/)

## 📄 Licencia

Este proyecto es parte de una evaluación técnica para ChatBet.

## 🙋‍♂️ Soporte

Para problemas y preguntas, referirse a:
- Documentación del código y comentarios inline
- Angular DevTools para debugging de signals y estado
- Herramientas de desarrollador del navegador para inspección WebSocket
- Logs de aplicación en consola para troubleshooting

---

**Construido con ❤️ por Daniel Sarmiento**  
*Desarrollador Full-Stack Senior & Especialista en Integración de IA*
