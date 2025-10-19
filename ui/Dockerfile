FROM freqtradeorg/frequi:latest

# Accept build arguments for FreqUI credentials
ARG FT_UI_USERNAME=admin
ARG FT_UI_PASSWORD=admin123

# Copy custom nginx configuration and bootstrap script
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY init-bots.js /etc/nginx/html/

# Replace placeholders with actual credentials
RUN sed -i "s/__FT_UI_USERNAME__/${FT_UI_USERNAME}/g" /etc/nginx/html/init-bots.js && \
    sed -i "s/__FT_UI_PASSWORD__/${FT_UI_PASSWORD}/g" /etc/nginx/html/init-bots.js && \
    sed -i '/<head>/a \  <script src="/init-bots.js"></script>' /etc/nginx/html/index.html

# Install apache2-utils for htpasswd, create password file, then clean up
RUN apk add --no-cache apache2-utils && \
    htpasswd -bc /etc/nginx/.htpasswd "${FT_UI_USERNAME}" "${FT_UI_PASSWORD}" && \
    # Verify that the htpasswd file was created and is not empty
    if [ ! -s /etc/nginx/.htpasswd ]; then \
        echo "Error: .htpasswd file not created or is empty." >&2; \
        exit 1; \
    fi && \
    # Ensure nginx user can read the password file
    chown nginx:nginx /etc/nginx/.htpasswd && \
    chmod 644 /etc/nginx/.htpasswd && \
    apk del apache2-utils
