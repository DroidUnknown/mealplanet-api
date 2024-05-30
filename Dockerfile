FROM python:3.9.9

# set the work directory
WORKDIR /app

# Add all files except ones in .dockerignore
ADD . /app

# install dependencies
RUN pip3 install -r requirements.txt

# run the app via gunicorn
ENTRYPOINT gunicorn -b 0.0.0.0:8000 api:app --reload
