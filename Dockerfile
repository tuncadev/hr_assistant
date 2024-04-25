# Use the official Python image as the base image
FROM python:3.10.12

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --verbose -r requirements.txt

# Copy the Streamlit app files into the container
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Command to run the Streamlit app when the container starts
CMD ["streamlit", "run", "app.py"]
