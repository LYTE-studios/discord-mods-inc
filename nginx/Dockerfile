FROM nginx:1.25-alpine

# Install required packages
RUN apk add --no-cache curl

# Remove default nginx config and user directive
RUN rm /etc/nginx/conf.d/default.conf && \
    sed -i '/user  nginx;/d' /etc/nginx/nginx.conf

# Create necessary directories with proper permissions
RUN mkdir -p /var/log/nginx /app/web/staticfiles /app/web/media && \
    chown -R nginx:nginx /var/log/nginx /app && \
    chmod -R 755 /app/web/staticfiles /app/web/media

# Copy custom nginx config
COPY --chown=nginx:nginx default.conf /etc/nginx/conf.d/

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost/health/ || exit 1

# Expose ports
EXPOSE 80 443

# Switch to non-root user
USER nginx

# Set permissions for nginx to write to /tmp
RUN mkdir -p /tmp/nginx && \
    chown -R nginx:nginx /tmp/nginx && \
    chmod -R 755 /tmp/nginx