FROM python:3.9

RUN mkdir /project_3

WORKDIR /project_3

ENV PYTHONPATH="/project_3"

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

#WORKDIR src

CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
