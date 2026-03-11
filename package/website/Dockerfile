# 第一阶段：构建前端项目（优化缓存、权限、版本）
FROM node:22.14-alpine as build-stage

WORKDIR /app

# 先复制依赖文件（利用Docker缓存，仅依赖变动时重新安装）
COPY --chown=frontend:nodejs package.json pnpm-lock.yaml* ./

# 配置pnpm（通过corepack管理，指定版本，避免全局安装冲突）
RUN corepack enable && corepack prepare pnpm@10.18.3 --activate
RUN pnpm config set registry https://registry.npmmirror.com \
    && pnpm config set fetch-retries 20

# 安装依赖（仅安装生产依赖，加速构建）
RUN NODE_ENV=production pnpm install --frozen-lockfile --verbose

# 复制项目源码（依赖安装完再复制，缓存生效）
COPY --chown=frontend:nodejs . .

# 构建生产版本（指定环境变量，确保生产模式）
RUN NODE_ENV=production pnpm run build \
    # 验证构建产物是否存在，避免空目录部署
    && test -d /app/dist && ls -la /app/dist || (echo "构建失败：dist目录不存在" && exit 1)

# 第二阶段：Nginx部署（优化配置、日志、权限）
FROM nginx:alpine as production-stage

# 配置Nginx日志（方便排查问题）
RUN mkdir -p /var/log/nginx/frontend \
    && touch /var/log/nginx/frontend/access.log \
    && touch /var/log/nginx/frontend/error.log \
    # 设置Nginx用户权限
    && chown -R nginx:nginx /var/log/nginx/frontend /var/cache/nginx

# 复制自定义Nginx配置（先验证配置合法性）
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
# RUN nginx -t -c /etc/nginx/nginx.conf || (echo "Nginx配置错误" && exit 1)

# 从构建阶段复制dist目录（仅复制必要文件，减少镜像体积）
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN chown -R nginx:nginx /usr/share/nginx/html

# 暴露80端口
EXPOSE 80

# 启动Nginx（指定配置，前台运行）
CMD ["nginx", "-g", "daemon off; error_log /var/log/nginx/frontend/error.log warn; access_log /var/log/nginx/frontend/access.log main;"]