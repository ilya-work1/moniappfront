FROM python
RUN mkdir /frontmoniapp
RUN chmod 777 /frontmoniapp
COPY . /frontmoniapp
WORKDIR /frontmoniapp
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
