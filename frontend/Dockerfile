# syntax=docker/dockerfile:1.7

# Stage 1: Production (serve prebuilt dist with nginx)
FROM nginx:alpine AS prod
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage 2: Development (Vite dev server)
FROM node:22-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
