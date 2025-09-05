# Use NVIDIA's CUDA base image with Ubuntu
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04
# FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install prerequisites
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    software-properties-common \
    git \
    vim \
    htop \
    nodejs \
    npm \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set Python3 as default
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Install code-server (VS Code Server)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install JupyterLab and comprehensive data science packages
RUN pip install --no-cache-dir \
    # Jupyter ecosystem
    jupyterlab \
    notebook \
    ipywidgets \
    jupyterlab-git \
    jupyterlab-lsp  \
    # Core data science libraries
    numpy \
    pandas \
    scipy \
    scikit-learn \
    # Visualization libraries
    matplotlib \
    seaborn \
    plotly \
    bokeh \
    altair \
    # Machine learning and AI
    tensorflow \
    torch \
    torchvision \
    torchaudio \
    transformers \
    datasets \
    # Deep learning utilities
    keras \
    xgboost \
    lightgbm \
    catboost \
    # Statistical analysis
    statsmodels \
    pingouin \
    # Data processing and utilities
    openpyxl \
    xlrd \
    h5py \
    pyarrow \
    fastparquet \
    # Database connectivity
    sqlalchemy \
    psycopg2-binary \
    pymongo \
    # Web scraping and APIs
    requests \
    beautifulsoup4 \
    scrapy \
    # Image processing
    pillow \
    opencv-python \
    imageio \
    # Natural language processing
    nltk \
    spacy \
    textblob \
    # Time series analysis
    prophet \
    # Geospatial analysis
    geopandas \
    folium \
    # Development and debugging tools
    jupyter-dash \
    ipdb \
    tqdm \
    # Configuration and environment
    python-dotenv \
    pyyaml \
    # Testing
    pytest \
    pytest-cov

# Create a non-root user
RUN useradd -m -s /bin/bash developer
USER developer
WORKDIR /home/developer

# Expose ports
# 8080 for VS Code Server
# 8888 for Jupyter Server
EXPOSE 8080 8888

# Create startup script with dynamic base URL support
RUN echo '#!/bin/bash\n\
echo "Starting VS Code Server on port 8080..."\n\
mkdir -p .config/code-server\n\
echo "bind-addr: 0.0.0.0:8080\n\
auth: none\n\
cert: false" > .config/code-server/config.yaml\n\
code-server &\n\
echo "Starting Jupyter Server on port 8888..."\n\
# Use JUPYTER_BASE_URL environment variable if set, otherwise default\n\
JUPYTER_BASE_URL=${JUPYTER_BASE_URL:-""}\n\
if [ -n "$JUPYTER_BASE_URL" ]; then\n\
    echo "Starting Jupyter with base URL: $JUPYTER_BASE_URL"\n\
    jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root \\\n\
        --ServerApp.token='"'"''"'"' --ServerApp.password='"'"''"'"' \\\n\
        --ServerApp.base_url="$JUPYTER_BASE_URL" \\\n\
        --ServerApp.allow_origin="*" \\\n\
        --ServerApp.disable_check_xsrf=True \\\n\
        --LabApp.base_url="$JUPYTER_BASE_URL"\n\
else\n\
    echo "Starting Jupyter with default configuration"\n\
    jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root \\\n\
        --ServerApp.token='"'"''"'"' --ServerApp.password='"'"''"'"'\n\
fi\n\
wait' > /tmp/start.sh && chmod +x /tmp/start.sh

CMD ["/tmp/start.sh"]