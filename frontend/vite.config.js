import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// Plugin to fix prop-types CommonJS to ESM conversion
const fixPropTypesPlugin = () => ({
  name: 'fix-prop-types',
  enforce: 'pre',
  transform(code, id) {
    // Transform prop-types imports in node_modules
    if (id.includes('node_modules') && code.includes("from 'prop-types'") || code.includes('from "prop-types"')) {
      // Replace CommonJS-style prop-types imports
      return code.replace(
        /import\s+PropTypes\s+from\s+['"]prop-types['"]/g,
        "import PropTypes from 'prop-types/index.js'"
      )
    }
    return null
  }
})

export default defineConfig({
  plugins: [
    fixPropTypesPlugin(),
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'favicon.ico'],
      manifest: {
        name: 'ILUMINATI SYSTEM',
        short_name: 'ILUMINATI',
        description: 'Transparentnosť pre slovenské podnikanie - Cross-border business intelligence',
        theme_color: '#0B4EA2',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/favicon.svg',
            sizes: 'any',
            type: 'image/svg+xml'
          },
          {
            src: '/favicon.ico',
            sizes: '48x48',
            type: 'image/x-icon'
          }
        ],
        start_url: '/',
        scope: '/',
        orientation: 'portrait-primary'
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 rok
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gstatic-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 rok
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /^http:\/\/localhost:8000\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 // 24 hodín
              },
              networkTimeoutSeconds: 10
            }
          }
        ]
      }
    })
  ],
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'prop-types'],
    esbuildOptions: {
      mainFields: ['module', 'main'],
      resolveExtensions: ['.mjs', '.js', '.jsx', '.ts', '.tsx']
    }
  },
  resolve: {
    dedupe: ['react', 'react-dom', 'prop-types']
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'graph-vendor': ['react-force-graph-2d', 'd3-force'],
          'utils': ['lucide-react']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    hmr: {
      overlay: true
    }
  }
})

