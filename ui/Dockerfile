FROM freqtradeorg/frequi:latest

COPY init-bots.js /usr/share/nginx/html/

RUN sed -i '/<head>/a \  <script src="init-bots.js"></script>' /usr/share/nginx/html/index.html
