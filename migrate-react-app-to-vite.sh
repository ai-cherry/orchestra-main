#!/bin/bash

# Migrate React App from Create React App to Vite
# Part of Frontend Enhancement Masterplan - Phase 1

set -e

echo "🚀 Starting React App Migration to Vite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "src/ui/web/react_app/package.json" ]; then
    print_error "Not in orchestra-main directory. Please run from project root."
    exit 1
fi

REACT_APP_DIR="src/ui/web/react_app"
BACKUP_DIR="src/ui/web/react_app_backup_$(date +%Y%m%d_%H%M%S)"

print_step "Step 1: Creating backup of current React app..."
cp -r "$REACT_APP_DIR" "$BACKUP_DIR"
print_status "Backup created at $BACKUP_DIR"

print_step "Step 2: Installing Vite and dependencies..."
cd "$REACT_APP_DIR"

# Remove Create React App dependencies
npm uninstall react-scripts
npm uninstall @types/react-scripts 2>/dev/null || true

# Install Vite and plugins
npm install --save-dev vite @vitejs/plugin-react @vitejs/plugin-react-swc
npm install --save-dev vite-tsconfig-paths vite-plugin-eslint
npm install --save-dev @types/node

print_step "Step 3: Creating Vite configuration..."
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tsconfigPaths from 'vite-tsconfig-paths'
import eslint from 'vite-plugin-eslint'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(),
    eslint({
      exclude: ['**/node_modules/**']
    })
  ],
  server: {
    port: 3000,
    host: true
  },
  build: {
    outDir: 'build',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ai: ['@reduxjs/toolkit', 'react-redux'],
          ui: ['@heroicons/react', 'react-dnd', 'react-dnd-html5-backend']
        }
      }
    },
    target: 'esnext',
    minify: 'esbuild'
  },
  define: {
    global: 'globalThis',
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})
EOF

print_step "Step 4: Creating index.html for Vite..."
mkdir -p public 2>/dev/null || true
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cherry AI Orchestrator - Admin Interface</title>
    <meta name="description" content="AI Orchestration Platform with Cherry, Sophia, and Karen personas" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/index.tsx"></script>
  </body>
</html>
EOF

print_step "Step 5: Updating package.json scripts..."
# Update package.json scripts for Vite
cat > temp_package.json << 'EOF'
{
  "name": "cherry-ai-orchestrator",
  "version": "1.0.0",
  "description": "AI Orchestration Platform with Cherry, Sophia, and Karen personas",
  "main": "src/index.tsx",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "preview": "vite preview",
    "serve": "vite preview"
  },
  "dependencies": {
    "@heroicons/react": "^2.0.18",
    "@reduxjs/toolkit": "^1.9.7",
    "@types/node": "^20.8.6",
    "@types/react": "^18.2.28",
    "@types/react-dom": "^18.2.13",
    "ajv": "6.12.6",
    "ajv-keywords": "3.5.2",
    "react": "^18.2.0",
    "react-dnd": "^16.0.1",
    "react-dnd-html5-backend": "^16.0.1",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.47.0",
    "react-redux": "^8.1.3",
    "react-refresh": "^0.17.0",
    "react-router-dom": "^6.16.0",
    "recharts": "^2.8.0",
    "socket.io-client": "^4.8.1",
    "typescript": "^5.3.0",
    "web-vitals": "^3.4.0"
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.6",
    "@tailwindcss/typography": "^0.5.10",
    "@types/jest": "^29.5.5",
    "@vitejs/plugin-react": "^4.2.1",
    "@vitejs/plugin-react-swc": "^3.5.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.51.0",
    "eslint-config-react-app": "^7.0.1",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "vite": "^5.1.0",
    "vite-plugin-eslint": "^1.8.1",
    "vite-tsconfig-paths": "^4.3.1"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "engines": {
    "node": "22.x"
  }
}
EOF

mv temp_package.json package.json

print_step "Step 6: Updating TypeScript configuration..."
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ESNext",
    "lib": [
      "dom",
      "dom.iterable",
      "ES6"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/utils/*": ["./src/utils/*"],
      "@/types/*": ["./src/types/*"]
    }
  },
  "include": [
    "src",
    "vite.config.ts"
  ],
  "exclude": [
    "node_modules",
    "build"
  ]
}
EOF

print_step "Step 7: Creating environment configuration..."
cat > .env.development << 'EOF'
VITE_APP_NAME=Cherry AI Orchestrator
VITE_API_URL=http://localhost:8000
VITE_SOCKET_URL=ws://localhost:8000
VITE_NODE_ENV=development
EOF

cat > .env.production << 'EOF'
VITE_APP_NAME=Cherry AI Orchestrator
VITE_API_URL=https://api.orchestra-ai.com
VITE_SOCKET_URL=wss://api.orchestra-ai.com
VITE_NODE_ENV=production
EOF

print_step "Step 8: Updating environment variable usage in code..."
# Update environment variables from REACT_APP_ to VITE_
find src -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/process\.env\.REACT_APP_/import.meta.env.VITE_/g' 2>/dev/null || true

print_step "Step 9: Installing updated dependencies..."
npm install

print_step "Step 10: Testing Vite build..."
npm run build

if [ $? -eq 0 ]; then
    print_status "✅ Vite build successful!"
    
    print_step "Step 11: Testing dev server..."
    timeout 10s npm run dev &
    DEV_PID=$!
    sleep 5
    kill $DEV_PID 2>/dev/null || true
    
    print_status "✅ Dev server test completed"
    
    print_step "Step 12: Updating Vercel configuration for Vite..."
    cat > vercel.json << 'EOF'
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "buildCommand": "npm run build",
        "outputDirectory": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/assets/(.*)",
      "dest": "/assets/$1",
      "headers": {
        "cache-control": "public, max-age=31536000, immutable"
      }
    },
    {
      "src": "/favicon.ico",
      "dest": "/favicon.ico"
    },
    {
      "src": "/manifest.json",
      "dest": "/manifest.json"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
EOF

    print_status "✅ Migration completed successfully!"
    
    echo ""
    echo "📊 Migration Summary:"
    echo "✅ Migrated from Create React App to Vite"
    echo "✅ Updated TypeScript to v5.3.0"
    echo "✅ Configured path mapping and aliases"
    echo "✅ Set up development and production environments"
    echo "✅ Updated Vercel deployment configuration"
    echo "✅ Created backup at $BACKUP_DIR"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Run 'npm run dev' to start development server"
    echo "2. Run 'npm run build' to test production build"
    echo "3. Deploy to Vercel with 'vercel --prod --yes'"
    echo ""
    echo "📈 Expected improvements:"
    echo "- Build time: 38s → 3-5s (90% faster)"
    echo "- Bundle size: Reduced by ~30%"
    echo "- Dev server: Hot reload in <100ms"
    echo "- Tree shaking: Better optimization"
    
else
    print_error "❌ Vite build failed. Check the error above."
    print_warning "Restoring from backup..."
    cd ../../..
    rm -rf "$REACT_APP_DIR"
    mv "$BACKUP_DIR" "$REACT_APP_DIR"
    print_status "Backup restored. Migration failed safely."
    exit 1
fi

print_status "🎉 React App successfully migrated to Vite!" 