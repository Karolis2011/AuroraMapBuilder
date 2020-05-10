# Dockerfile - this is a comment. Delete me if you want.
FROM python:3.8
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt


ENV GITHUB_SECRET H9hU5HNWJRvQYum2fXLJ
ENV SERVER_NAME 127.0.0.1:5478
EXPOSE 5478
ENTRYPOINT ["python"]
CMD ["mapServer.py"]