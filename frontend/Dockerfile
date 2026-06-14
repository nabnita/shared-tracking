# Build stage
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Replace ${PORT} dynamically and start nginx
CMD sed -i "s/\${PORT}/$PORT/g" /etc/nginx/conf.d/default.conf && nginx -g "daemon off;"
