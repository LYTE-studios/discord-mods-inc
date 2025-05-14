FROM nginx:1.25-alpine

# Install required packages
RUN apk add --no-cache curl

# Remove default nginx config and user directive
RUN rm /etc/nginx/conf.d/default.conf && \
    sed -i '/user  nginx;/d' /etc/nginx/nginx.conf

# Create necessary directories with proper permissions
RUN mkdir -p /var/log/nginx \
            /app/web/staticfiles \
            /app/web/media \
            /var/cache/nginx \
            /var/cache/nginx/client_temp \
            /var/cache/nginx/proxy_temp \
            /var/cache/nginx/fastcgi_temp \
            /var/cache/nginx/uwsgi_temp \
            /var/cache/nginx/scgi_temp && \
    chown -R nginx:nginx /var/log/nginx \
                        /app \
                        /var/cache/nginx \
                        /var/cache/nginx/client_temp \
                        /var/cache/nginx/proxy_temp \
                        /var/cache/nginx/fastcgi_temp \
                        /var/cache/nginx/uwsgi_temp \
                        /var/cache/nginx/scgi_temp && \
    chmod -R 755 /app/web/staticfiles \
                 /app/web/media \
                 /var/cache/nginx \
                 /var/cache/nginx/client_temp \
                 /var/cache/nginx/proxy_temp \
                 /var/cache/nginx/fastcgi_temp \
                 /var/cache/nginx/uwsgi_temp \
                 /var/cache/nginx/scgi_temp

# Copy custom nginx config
COPY --chown=nginx:nginx default.conf /etc/nginx/conf.d/

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost/health/ || exit 1

# Expose ports
EXPOSE 80 443

# Switch to non-root user
USER nginx