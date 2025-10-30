FROM adminer:latest

# Create directory for plugins
RUN mkdir -p /var/www/html/plugins-enabled

# Copy the combined plugin file
COPY docker/login-ip.php /var/www/html/plugins-enabled/login-ip.php
