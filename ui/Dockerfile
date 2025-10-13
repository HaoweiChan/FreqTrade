FROM freqtradeorg/frequi:latest

# Copy our bootstrap script into the path actually served by nginx and inject it into index.html
COPY init-bots.js /etc/nginx/html/

RUN sed -i '/<head>/a \  <script src="/init-bots.js"></script>' /etc/nginx/html/index.html
