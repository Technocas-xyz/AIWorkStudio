FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Build-time env: empty VITE_API_URL so frontend uses relative URLs (proxied by nginx)
ENV VITE_API_URL=""

# Expose port
EXPOSE 3000

# Start dev server with HMR disabled for production-like serving
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]
