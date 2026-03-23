# ── 构建阶段 ──
FROM node:18-alpine AS build-stage

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm install

# 复制源码并构建
COPY . .
RUN npm run build

# ── 生产服务阶段 ──
FROM nginx:stable-alpine AS production-stage

# 将构建产物复制到 Nginx 静态目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置（解决前端路由 History 模式 404 问题）
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
