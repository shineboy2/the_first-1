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

# نصب PM2 برای مدیریت سرور
RUN npm install -g pm2

# کپی کردن built files از builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json .

# Expose port
EXPOSE 3000

# Start سرور
CMD ["npm", "start"]
