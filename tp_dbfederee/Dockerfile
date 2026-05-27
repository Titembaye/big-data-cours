FROM postgres:15

RUN echo 'Acquire::By-Hash "no";' > /etc/apt/apt.conf.d/99no-hash \
    && apt-get update && apt-get install -y \
    postgresql-15-mysql-fdw \
    && rm -rf /var/lib/apt/lists/*
