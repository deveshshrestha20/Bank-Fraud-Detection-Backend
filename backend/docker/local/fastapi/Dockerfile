ARG PYTHON_VERSION=3.13.1

FROM python:${PYTHON_VERSION}-slim-bookworm AS python

# Stage 1: build dependency wheels
FROM python AS python-build-stage

RUN apt-get update && apt-get install \
  --no-install-recommends -y \
  build-essential \
  libpq-dev

COPY ./backend/requirements.txt .

RUN pip wheel --wheel-dir /usr/src/app/wheels \
  -r requirements.txt \
  --no-cache-dir

# Stage 2: Python run stage
FROM python AS python-run-stage

ARG APP_HOME=/src
ARG APP_USER=fastapi
ARG APP_GROUP=fastapi

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install --no-install-recommends -y \
  sudo git bash-completion nano ssh \
  gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN groupadd -r ${APP_GROUP} && \
  useradd -r -g ${APP_GROUP} -d ${APP_HOME} -m ${APP_USER}

RUN mkdir -p ${APP_HOME}/backend/app/logs && \
  chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}/backend/app/logs && \
  chmod 775 ${APP_HOME}/backend/app/logs

COPY --from=python-build-stage /usr/src/app/wheels /wheels/

RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

COPY --chown=${APP_USER}:{APP_GROUP} ./backend/docker/local/fastapi/entrypoint.sh /entrypoint.sh
COPY --chown=${APP_USER}:{APP_GROUP} ./backend/docker/local/fastapi/start.sh /start.sh






COPY --chown=${APP_USER}:${APP_GROUP} . ${APP_HOME}

USER ${APP_USER}

ENTRYPOINT [ "/entrypoint.sh" ]


