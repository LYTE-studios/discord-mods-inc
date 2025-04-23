FROM postgres:15

# Copy configuration files
COPY postgresql.conf /etc/postgresql/postgresql.conf
COPY init.sql /docker-entrypoint-initdb.d/

# Set proper permissions
RUN chown postgres:postgres /etc/postgresql/postgresql.conf /docker-entrypoint-initdb.d/init.sql