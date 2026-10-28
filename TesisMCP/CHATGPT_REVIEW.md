# TesisMCP — guía para revisión

Este proyecto conserva el prototipo visual como modo de demostración y añade acceso y selección de proyectos conectados al backend Django. El recorrido real todavía no integra el editor ni la biblioteca.

## Tecnologías

- React 19
- TypeScript
- Vite
- Tailwind CSS 4
- CSS global en `src/index.css`

## Archivos principales

- `src/App.tsx`: sesión, selección de proyecto y entrada a la demo.
- `src/DemoApp.tsx`: cinco pantallas de demostración con datos de ejemplo.
- `src/api/`: transporte y funciones de sesión y proyectos.
- `src/features/`: acceso y espacio conectado del proyecto.
- `src/index.css`: sistema visual, tokens y estilos de toda la aplicación.
- `src/main.tsx`: punto de entrada de React.
- `package.json`: scripts y dependencias.

## Pantallas

Dentro del modo demostración, la navegación lateral permite abrir:

1. Panel principal del tesista.
2. Editor metodológico de tres paneles.
3. Biblioteca científica.
4. Dashboard del asesor.
5. Revisión del asesor.

La aplicación real inicia consultando la sesión y ofrece acceso, selección de proyecto y un espacio inicial conectado. El editor metodológico más detallado sigue dentro de la demo.

## Ejecución local

Requiere Node.js y pnpm.

```bash
pnpm install
pnpm dev
```

En desarrollo, Vite envía `/api` a `http://127.0.0.1:8000`; se puede cambiar con `TESISMCP_API_TARGET`. Django debe ejecutarse con configuración local compatible con cookies y CSRF.

Para crear una compilación de producción:

```bash
pnpm build
```

## Puntos sugeridos para analizar

- Arquitectura y reutilización de componentes.
- Accesibilidad y navegación mediante teclado.
- Adaptación a resoluciones menores.
- Integración futura del editor canónico y biblioteca con sus contratos backend.
- Verificación en navegador de acceso, cookies y proyecto con cuenta real.
- Integración real de fuentes PDF y asistente metodológico.
