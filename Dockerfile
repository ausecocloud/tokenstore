FROM python:3.6-slim-stretch



RUN pip install --no-cache --upgrade pip setuptools \
 && pip install --no-cache --upgrade \
     gunicorn \
     PasteScript \
     openapi-core==0.6.0 \
     psycopg2-binary \
     redis \
     https://github.com/ausecocloud/pyramid_oidc/archive/b1e5db9092f066f4a815515c4d7001801303c541.zip \
     https://github.com/ausecocloud/pyramid_cors/archive/c79785aff56456bf7543dd17e766492b3953f037.zip \
     https://github.com/ausecocloud/pyramid_openapi/archive/7425984b9444fe64974f877b1a788c48ee834bd2.zip

RUN pip install --no-cache \
    https://github.com/ausecocloud/tokenstore/archive/003c26c89f09dcaf22b6c98ae39f7af29edda58b.zip

COPY development.ini /etc/tokenstore/tokenstore.ini

CMD ["gunicorn", "--paste", "/etc/tokenstore/tokenstore.ini", "--bind=0.0.0.0:6543"]
