FROM nginx:1.25-alpine

# Install required packages
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Create necessary directories
RUN mkdir -p /var/log/nginx /app/web/staticfiles /app/web/media && \
    chown -R nginx:nginx /var/log/nginx /app

# Copy custom nginx config
COPY default.conf /etc/nginx/conf.d/

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost/health/ || exit 1

# Expose ports
EXPOSE 80 443

# Use non-root user
USER nginx