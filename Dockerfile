FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

# Install Python dependencies
COPY requirements-strategy.txt .
RUN pip install --no-cache-dir -r requirements-strategy.txt

# Create necessary directories
RUN mkdir -p /freqtrade/user_data/strategies

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

EXPOSE 8080

CMD ["trade", "--config", "/freqtrade/user_data/config.json"]