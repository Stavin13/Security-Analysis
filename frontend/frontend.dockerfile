# Build stage
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Set npm config for faster installs
ENV npm_config_loglevel=error \
    npm_config_progress=false \
    npm_config_fund=false \
    npm_config_audit=false

# Copy package files
COPY package*.json ./

# Install dependencies with clean npm cache and only production dependencies
RUN npm cache clean --force && \
    npm ci --only=production --prefer-offline

# Copy frontend source code
COPY . .

# Build the app
RUN npm run build

# Production stage - using nginx for better performance
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 