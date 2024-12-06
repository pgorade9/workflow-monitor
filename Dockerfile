FROM python:3.12
RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip install -r requirements.txt
EXPOSE 80
ENTRYPOINT ["uvicorn","src.app:app","--host=0.0.0.0", "--port=80"]