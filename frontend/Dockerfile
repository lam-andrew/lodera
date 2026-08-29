# Lodera frontend — React + TypeScript (Vite dev server)
FROM node:20-slim

WORKDIR /app

# Install dependencies first for layer caching.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

# Dev server bound to all interfaces (see vite.config.ts) so the host can reach it.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
