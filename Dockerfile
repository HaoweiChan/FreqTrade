FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

# Install Python dependencies
COPY requirements-strategy.txt .
RUN pip install --no-cache-dir -r requirements-strategy.txt

# Create necessary directories
# Remove any existing symlink and create as directory
RUN rm -f /freqtrade/user_data/strategies && \
    mkdir -p /freqtrade/user_data/strategies

# Copy and extract strategies
COPY strategies.tar.gz .
RUN tar -xzf strategies.tar.gz -C /freqtrade/user_data/strategies && \
    rm strategies.tar.gz

# Remove any .DS_Store files from strategies
RUN find /freqtrade/user_data/strategies -name ".DS_Store" -type f -delete

# Copy configuration (but not strategies)
COPY user_data/config.json /freqtrade/user_data/config.json

# Create logs directory
RUN mkdir -p /freqtrade/user_data/logs

# Copy entrypoint script to fix strategies symlink issue
COPY --chmod=+x docker-entrypoint.sh /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["freqtrade", "trade", "--config", "/freqtrade/user_data/config.json"]