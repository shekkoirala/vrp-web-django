FROM python:3.7.3
MAINTAINER nitesh
ENV PYTHONUNBUFFERED 1

RUN mkdir /vrp


WORKDIR /vrp

COPY . /vrp

# RUN pip install -r requirements.txt
RUN pip install -r requirements.txt

RUN python manage.py migrate --noinput
# RUN python manage.py initadmin

EXPOSE 8090
ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:8090"]
