FROM freqtradeorg/frequi:latest

# Accept build arguments for FreqUI credentials
ARG FT_UI_USERNAME=admin
ARG FT_UI_PASSWORD=admin123

# Copy our bootstrap script into the path actually served by nginx and inject it into index.html
COPY init-bots.js /etc/nginx/html/

# Replace placeholders with actual credentials
RUN sed -i "s/__FT_UI_USERNAME__/${FT_UI_USERNAME}/g" /etc/nginx/html/init-bots.js && \
    sed -i "s/__FT_UI_PASSWORD__/${FT_UI_PASSWORD}/g" /etc/nginx/html/init-bots.js && \
    sed -i '/<head>/a \  <script src="/init-bots.js"></script>' /etc/nginx/html/index.html
