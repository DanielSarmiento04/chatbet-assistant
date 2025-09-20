# ChatBet Frontend

Esta es una interfaz de chat donde puedes hablar con un bot sobre apuestas deportivas. Está construido con Angular 19 y se ve bastante moderno gracias a Material Design.

## Qué hace

**Lo principal:** Chateas con un bot que sabe sobre apuestas deportivas. Pregúntale sobre cuotas, partidos, o cómo hacer apuestas.

**Cosas del chat que funcionan:**
- Los mensajes aparecen al instante (conexión WebSocket)
- La página se desplaza hacia abajo automáticamente cuando llegan mensajes nuevos (pero se detiene si estás desplazándote hacia arriba)
- Puedes ver cuando el bot está escribiendo
- Los mensajes se ven bien con texto en negrita y listas
- Tu historial de conversación se mantiene ahí
- Si algo se rompe, te dice qué salió mal

**Otras cosas útiles:**
- Funciona en tu teléfono
- Muestra si estás conectado o no
- Se ve bien tanto en modo claro como oscuro
- Puedes navegar solo con tu teclado

## Cómo está construido

**Lo que usamos:**
- Angular 19 (la versión más reciente con componentes standalone)
- Angular Material para la UI (el sistema de diseño de Google)
- WebSocket para chat en tiempo real
- TypeScript porque JavaScript normal se vuelve un desastre
- Bun en lugar de npm (es más rápido)

**Cómo está organizado el código:**
```
src/app/
├── components/        # Piezas de UI que puedes reutilizar
│   ├── chat-interface/ # La ventana principal del chat
│   ├── chat-input/    # Donde escribes mensajes
│   ├── message-bubble/ # Mostrar mensajes individuales
│   └── header/        # Navegación superior
├── services/          # La lógica que hace que las cosas funcionen
│   ├── auth.service.ts    # Cosas de login/logout
│   ├── chat.service.ts    # Manejar conversaciones
│   ├── websocket.service.ts # Conexión en tiempo real
│   └── api.service.ts     # Hablar con el backend
├── models/           # Tipos de TypeScript (mantiene las cosas organizadas)
└── pages/           # Diferentes pantallas en la app
```

## Ponerlo a funcionar

**Lo que necesitas primero:**
- Node.js (versión 18 o más nueva)
- Bun (es como npm pero más rápido)
- Git

**Para empezar a desarrollar:**
```bash
# Obtener el código
git clone https://github.com/DanielSarmiento04/chatbet-assistant.git
cd chatbet-assistant/chatbet-frontend

# Instalar todo
bun install

# Iniciar el servidor de desarrollo
bun run start

# Abrir http://localhost:4200 en tu navegador
```

**Otros comandos que podrías necesitar:**
```bash
bun run build         # Construir para producción
bun run test          # Ejecutar pruebas
bun run lint          # Verificar calidad de código
```

## Cómo habla con el backend

**Conexión WebSocket:**
El frontend se conecta a `ws://localhost:8000/ws/chat` y envía mensajes así:

```typescript
{
  type: 'message',
  data: {
    content: "¿Cuáles son los partidos de fútbol de hoy?",
    session_id: "algún-id-único"
  }
}
```

El backend responde con:
```typescript
{
  type: 'response',
  data: {
    content: "Aquí están los partidos de hoy...",
    message_id: "otro-id-único",
    is_final: true
  }
}
```

**Llamadas regulares a la API:**
- `GET /api/health` - Verificar si el backend está vivo
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/chat/sessions` - Obtener tu historial de chat

## Componentes principales

**ChatInterface:** La ventana principal del chat donde pasa todo. Maneja el desplazamiento, muestra indicadores de escritura, y se conecta al WebSocket.

**MessageBubble:** Muestra mensajes individuales. Puede renderizar markdown (texto en negrita, listas, etc.) y estiliza los mensajes de manera diferente para ti vs el bot.

**ChatInput:** El área de texto donde escribes. Crece mientras escribes más texto y envía mensajes cuando presionas Enter.

## Cómo funciona la autenticación

1. Cuando visitas el sitio, verifica si ya estás logueado
2. Si sí, se conecta al WebSocket y puedes empezar a chatear
3. Si no, necesitas hacer login primero
4. Una vez logueado, tu sesión se guarda para que no tengas que hacer login otra vez

El servicio de autenticación mantiene registro de si estás logueado y maneja el proceso de login/logout.

## La conexión WebSocket

Así es como los mensajes aparecen al instante. El frontend abre una conexión WebSocket al backend y:

- Envía tus mensajes inmediatamente
- Recibe respuestas del bot en tiempo real
- Muestra cuando el bot está escribiendo
- Se reconecta automáticamente si se cae la conexión
- Muestra el estado de conexión (conectado/desconectado)

## Cómo funciona el manejo de estado

Usamos el nuevo sistema de Signals de Angular en lugar de observables anticuados. Es más simple:

```typescript
// Estos actualizan automáticamente la UI cuando cambian
messages = signal<ChatMessage[]>([])
isConnected = signal<boolean>(false)
isTyping = signal<boolean>(false)

// Esto se actualiza automáticamente cuando cambian los mensajes
hasMessages = computed(() => this.messages().length > 0)
```

## Qué pasa cuando envías un mensaje

1. Escribes algo y presionas Enter
2. El mensaje se agrega al chat inmediatamente
3. WebSocket lo envía al backend
4. La UI muestra un indicador de carga
5. El backend lo procesa y envía una respuesta
6. La respuesta aparece en el chat
7. La página se desplaza hacia abajo automáticamente (a menos que estuvieras desplazándote hacia arriba)

## Estilos y temas

Usa Material Design 3 con colores personalizados. El tema cambia automáticamente entre claro y oscuro basado en las preferencias de tu sistema.

Todo es responsivo y funciona en teléfonos. Usamos CSS Grid y Flexbox para los layouts.

## Pruebas

```bash
# Ejecutar todas las pruebas
bun run test

# Ejecutar una prueba específica
bun run test -- --include="**/chat.service.spec.ts"

# Ver cobertura de pruebas
bun run test -- --coverage
```

Las pruebas cubren los servicios principales (auth, chat, websocket) y componentes clave.

## Construir para producción

```bash
# Crear build de producción
bun run build:prod

# Los archivos van en la carpeta dist/
# Puedes servirlos con cualquier servidor web
```

**Configuración de entorno:**
Crear archivos de entorno para diferentes configuraciones:

```typescript
// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://tu-api.com',
  wsUrl: 'wss://tu-api.com/ws'
};
```

## Problemas comunes y soluciones

**WebSocket no se conecta:**
- Verifica si el backend está corriendo: `curl http://localhost:8000/api/health`
- Asegúrate de que la URL del WebSocket sea correcta
- Revisa la consola del navegador para mensajes de error

**El build falla:**
```bash
# Limpiar todo y empezar de nuevo
rm -rf node_modules bun.lockb
bun install
```

**La página carga pero nada funciona:**
- Revisa la pestaña de network del navegador para requests fallidos
- Busca errores de JavaScript en la consola
- Asegúrate de que los endpoints de la API sean alcanzables

**La autenticación no funciona:**
- Verifica si el endpoint de login retorna la respuesta correcta
- Verifica que los tokens de auth se estén guardando/enviando correctamente
- Busca errores 401/403 en la pestaña de network

## Notas de rendimiento

La app carga rápido porque:
- Usa lazy loading para diferentes páginas
- Los bundles están optimizados y tree-shaken
- Estrategia OnPush de detección de cambios de Angular
- Los Signals actualizan solo lo que cambió

Rendimiento típico:
- La página carga en menos de 1.5 segundos
- WebSocket se conecta en menos de 100ms
- Los mensajes aparecen en menos de 50ms

## Cosas de seguridad

- Toda la comunicación está encriptada (HTTPS/WSS)
- La autenticación usa tokens JWT
- La entrada del usuario está sanitizada para prevenir XSS
- CORS está configurado apropiadamente
- No hay datos sensibles en localStorage

## Contribuir

Si quieres ayudar:

1. Haz fork del repo
2. Crea una rama: `git checkout -b arreglar-algo`
3. Haz tus cambios
4. Prueba que todo funcione
5. Commit: `git commit -m "Arreglar algo"`
6. Push y crea un pull request

**Estilo de código:**
- Usa modo estricto de TypeScript
- Sigue la guía de estilo de Angular
- Ejecuta `bun run lint` antes de hacer commit
- Escribe pruebas para nuevas funcionalidades

---

Construido por Daniel Sarmiento
