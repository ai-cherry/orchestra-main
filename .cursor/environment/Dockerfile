FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    pulumi=3.50.0 \
    python3-pip

RUN pip3 install \
    weaviate-client \
    pinecone-client \
    psycopg2-binary \
    redis
