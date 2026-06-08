FROM node:20-slim AS builder

WORKDIR /app

# کپی کردن package files
COPY package*.json ./

# نصب dependencies
RUN npm install

# کپی کردن کل پروژه
COPY . .

# Build پروژه (بدون نیاز به NEXT_PUBLIC_API_URL در build time)
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

# حذف هر config.js قدیمی که ممکن است در build time ساخته شده باشد
RUN rm -f /app/public/config.js

# Create runtime config generation script directly in image
RUN echo '#!/bin/sh' > /usr/local/bin/generate-config.sh && \
    echo '# Remove old config.js if exists' >> /usr/local/bin/generate-config.sh && \
    echo 'rm -f /app/public/config.js' >> /usr/local/bin/generate-config.sh && \
    echo '# Generate new config.js from template with current environment variables' >> /usr/local/bin/generate-config.sh && \
    echo 'envsubst < /app/public/config.template.js > /app/public/config.js' >> /usr/local/bin/generate-config.sh && \
    echo 'echo "Generated config.js with API_URL: $NEXT_PUBLIC_API_URL"' >> /usr/local/bin/generate-config.sh && \
    chmod +x /usr/local/bin/generate-config.sh

# Change ownership of app directory so the node user can write config.js at runtime
RUN chown -R node:node /app

USER node

# Expose port
EXPOSE 3001

ENV PORT=3001

# Generate runtime config and start server
CMD ["/bin/sh", "-c", "generate-config.sh && npm start"]
