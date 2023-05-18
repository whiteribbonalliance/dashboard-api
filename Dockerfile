FROM python:3.10

WORKDIR /backend

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

EXPOSE 80
EXPOSE 8080

ARG COMMIT_ID="No commit ID specified"
ENV COMMIT_ID=$COMMIT_ID

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
