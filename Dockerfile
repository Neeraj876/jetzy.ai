FROM python:3.13-slim-bookworm

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit will run on
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "main.py"]
