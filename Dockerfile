# Use AWS Lambda Python 3.13 as the base image
FROM public.ecr.aws/lambda/python:3.13
# Accept API key as a build argument
ARG GEMINI_API_KEY
ARG PINECONE_API_KEY
ARG APPSYNC_URL
ENV GEMINI_API_KEY=$GEMINI_API_KEY
ENV PINECONE_API_KEY=$PINECONE_API_KEY
ENV APPSYNC_URL=$APPSYNC_URL
# Set working directory to the Lambda function root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy only requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .


# Set the CMD to your Lambda handler
CMD [ "main.handler" ]
