FROM freqtradeorg/frequi:latest

# No build arguments needed - authentication removed

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Remove default server config from conf.d to avoid conflicts
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom entrypoint wrapper
COPY docker-entrypoint-wrapper.sh /
RUN chmod +x /docker-entrypoint-wrapper.sh

COPY init-bots.js /etc/nginx/html/

# Inject UI credentials from build arguments into init-bots.js
ARG FT_UI_USERNAME=fq
ARG FT_UI_PASSWORD=fq
RUN sed -i "s/__FT_UI_USERNAME__/${FT_UI_USERNAME}/g" /etc/nginx/html/init-bots.js && \
    sed -i "s/__FT_UI_PASSWORD__/${FT_UI_PASSWORD}/g" /etc/nginx/html/init-bots.js && \
    sed -i '/<head>/a \  <script src="/init-bots.js"></script>' /etc/nginx/html/index.html

# No authentication - removed auth setup

# Use custom entrypoint that ensures DNS is configured
ENTRYPOINT ["/docker-entrypoint-wrapper.sh"]
CMD ["nginx", "-g", "daemon off;"]
