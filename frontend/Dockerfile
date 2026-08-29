# Lodera frontend — React + TypeScript (Vite dev server)
FROM node:26-slim

WORKDIR /app

# Install dependencies first for layer caching.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# The node image ships a non-root `node` user; run as it (Trivy DS-0002).
RUN chown -R node:node /app
USER node

EXPOSE 5173

# Report container health by fetching the dev server's index (Trivy DS-0026).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://localhost:5173').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# Dev server bound to all interfaces (see vite.config.ts) so the host can reach it.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
