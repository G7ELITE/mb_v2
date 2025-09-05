import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  
  return {
    plugins: [react()],
    // Configurações de desenvolvimento (Vite dev server)
    server: !isProduction ? {
      host: '0.0.0.0',
      port: 5173,
      strictPort: false,
      allowedHosts: [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '.ngrok-free.app',
        '.ngrok.io',
        'a125b64f17ef.ngrok-free.app'
      ],
      hmr: {
        port: 5173
      },
      proxy: {
        // Todas as rotas /api/* (incluindo /api/rag/*)
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
          ws: true // Para WebSockets/Server-Sent Events
        },
        // Health check
        '/health': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false
        },
        // Engine (orquestrador)
        '/engine': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false
        },
        // Channels (telegram, whatsapp)
        '/channels': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false
        },
        // Root routes para compatibility
        '/leads': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false
        },
        '/tools': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false
        }
      }
    } : undefined,
    // Configurações de build para produção
    build: isProduction ? {
      outDir: 'dist',
      sourcemap: false,
      minify: 'esbuild',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom']
          }
        }
      }
    } : undefined,
    
    preview: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: false
    },
    define: {
      global: 'globalThis'
    }
  }
})
