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
            /var/cache/nginx/scgi_temp \
            /var/run && \
    chown -R nginx:nginx /var/log/nginx \
                        /app \
                        /var/cache/nginx \
                        /var/cache/nginx/client_temp \
                        /var/cache/nginx/proxy_temp \
                        /var/cache/nginx/fastcgi_temp \
                        /var/cache/nginx/uwsgi_temp \
                        /var/cache/nginx/scgi_temp \
                        /var/run && \
    chmod -R 755 /app/web/staticfiles \
                 /app/web/media \
                 /var/cache/nginx \
                 /var/cache/nginx/client_temp \
                 /var/cache/nginx/proxy_temp \
                 /var/cache/nginx/fastcgi_temp \
                 /var/cache/nginx/uwsgi_temp \
                 /var/cache/nginx/scgi_temp \
                 /var/run

# Copy custom nginx config
COPY --chown=nginx:nginx default.conf /etc/nginx/conf.d/

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost/health/ || exit 1

# Expose ports
EXPOSE 80 443

# Update nginx config to use pid file in writable directory
RUN sed -i 's#pid /var/run/nginx.pid;#pid /var/run/nginx.pid;#g' /etc/nginx/nginx.conf && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid && \
    chmod 644 /var/run/nginx.pid

# Switch to non-root user
USER nginx