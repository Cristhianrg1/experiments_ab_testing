FROM python:3.9

RUN apt-get update -y && \
    apt-get install -y libzmq3-dev && \
    apt-get clean

RUN pip install pipenv

WORKDIR /ab_testing_project

COPY Pipfile Pipfile.lock .env ./

RUN pipenv install --deploy --ignore-pipfile

COPY . .

EXPOSE 5000

CMD ["pipenv", "run", "python", "main.py"]