FROM python:3.12
RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip install -r requirements.txt
EXPOSE 8080
ENTRYPOINT ["uvicorn","app:app","--host=127.0.0.1", "--port=8080"]