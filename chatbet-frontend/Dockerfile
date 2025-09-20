# Stage 1: Build the Angular app
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copy package files
COPY package.json  ./

# Install dependencies (including dev dependencies for build)
RUN npm install

# Copy source code and config files
COPY ./src/ ./src/
COPY ./angular.json ./
COPY ./tsconfig.json ./
COPY ./tsconfig.app.json ./
COPY ./tsconfig.spec.json ./
COPY ./public/ ./public/

# Build the Angular app for production
RUN npm run build

# Stage 2: Serve the Angular app using NGINX
FROM nginx:alpine AS production-stage

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the built Angular app from the previous stage to NGINX's HTML folder
COPY --from=build-stage /app/dist/chatbet-frontend/browser /usr/share/nginx/html

# Copy custom NGINX configuration
COPY proxy/nginx.conf /etc/nginx/nginx.conf
COPY proxy/conf.d/default.conf /etc/nginx/conf.d/default.conf

# Copy SSL certificates (if needed)
COPY proxy/ssl/ /etc/nginx/ssl/

# Expose ports
EXPOSE 80
EXPOSE 443

# Start NGINX server
CMD ["nginx", "-g", "daemon off;"]
