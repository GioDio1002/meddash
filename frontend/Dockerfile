FROM oven/bun:1.2 AS builder

WORKDIR /app

COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile

COPY frontend/ .
RUN bun run build

FROM nginx:1.29-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
