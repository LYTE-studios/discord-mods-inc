FROM nginx:1.25

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Create necessary directories
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Copy custom nginx config
COPY default.conf /etc/nginx/conf.d/

# Create static and media directories
RUN mkdir -p /app/static /app/media && \
    chown -R nginx:nginx /app

EXPOSE 80