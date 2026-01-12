# Frontend Dockerfile for Railway deployment

# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Define build arguments for Vite environment variables
ARG VITE_API_URL
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_APP_NAME
ARG VITE_APP_VERSION

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_APP_VERSION=$VITE_APP_VERSION

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application (environment variables are baked in here)
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy nginx configuration
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Railway sets PORT environment variable
ENV PORT=80



# Expose the port
EXPOSE ${PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
