# Use Miniconda base image
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Copy environment files
COPY conda_requirements.txt pip_requirements.txt ./

# Add conda-forge channel and install dependencies
RUN conda config --add channels conda-forge && \
    conda config --set channel_priority strict && \
    conda create --name myenv --file conda_requirements.txt -y && \
    echo "source activate myenv" > ~/.bashrc && \
    /bin/bash -c "source activate myenv && pip install -r pip_requirements.txt"

# Ensure the environment is activated for subsequent commands
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Copy application files
COPY . .

# Expose the API port
EXPOSE 8000

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
