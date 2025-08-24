# Use NVIDIA's CUDA base image with Ubuntu
# FROM nvidia/cuda:12.4.1-devel-ubuntu22.04
FROM ubuntu:22.04

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

# Install JupyterLab
RUN pip install --no-cache-dir \
    jupyterlab \
    notebook \
    ipywidgets \
    numpy \
    pandas \
    matplotlib \
    seaborn

# Create a non-root user
RUN useradd -m -s /bin/bash developer
USER developer
WORKDIR /home/developer

# Configure code-server
RUN mkdir -p /home/developer/.config/code-server
RUN echo 'bind-addr: 0.0.0.0:8080\n\
auth: none\n\
cert: false' > /home/developer/.config/code-server/config.yaml

# Expose ports
# 8080 for VS Code Server
# 8888 for Jupyter Server
EXPOSE 8080 8888

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting VS Code Server on port 8080..."\n\
code-server &\n\
echo "Starting Jupyter Server on port 8888..."\n\
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''\n\
wait' > start.sh && chmod +x start.sh

CMD ["./start.sh"]