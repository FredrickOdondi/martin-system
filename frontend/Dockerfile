# Frontend Dockerfile for Railway deployment

# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy nginx configuration
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Use envsubst to replace PORT_PLACEHOLDER with actual PORT at runtime
# Railway sets PORT environment variable
ENV PORT=80

# Create startup script that handles the PORT variable
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-replace-port.sh && \
    echo 'sed -i "s/PORT_PLACEHOLDER/$PORT/g" /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.d/30-replace-port.sh && \
    chmod +x /docker-entrypoint.d/30-replace-port.sh

# Expose the port
EXPOSE ${PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
