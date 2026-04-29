FROM node:20-slim AS builder

WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# کپی کردن package files
COPY package*.json ./

# نصب dependencies
RUN npm install

# کپی کردن کل پروژه
COPY . .

# Build پروژه
RUN npm run build

# Runtime stage
FROM node:20-slim

WORKDIR /app

# Install envsubst for runtime config generation
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*

# نصب PM2 برای مدیریت سرور
RUN npm install -g pm2

# کپی کردن built files از builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json .

# Copy runtime config generation script
COPY generate-config.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-config.sh

# Expose port
EXPOSE 3002

ENV PORT=3002

# Generate runtime config and start server
CMD ["/bin/sh", "-c", "generate-config.sh && npm start"]
