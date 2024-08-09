# Stage 1: Build the frontend
FROM node:20 AS frontend-builder

WORKDIR /app/frontend

COPY /src/frontend/package*.json ./

RUN npm install

COPY /src/frontend/ .

RUN npm run build

# Debugging step
RUN ls -la /app/frontend

# Stage 2: Build the backend and serve the application
FROM python:3.10

WORKDIR /app/backend

COPY /src/backend/requirements.txt .

RUN apt-get update && \
    apt-get install -y ffmpeg

RUN pip install -r requirements.txt

COPY /src/backend/ .

# Copy the built frontend files to the backend static directory
COPY --from=frontend-builder /app/frontend/dist /app/backend/static

RUN mkdir /app/backend/data

# Expose port 9000 for the application
EXPOSE 9000

# Command to run the backend application
CMD ["python", "main.py"]
