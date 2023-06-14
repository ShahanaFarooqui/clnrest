FROM python:3.8 AS build

WORKDIR /clnrest

COPY . /clnrest

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install pyinstaller && \
    pyinstaller --onefile cln_rest.py && \
    pyinstaller --onefile clnrest.py

FROM scratch AS export-stage

COPY --from=build /clnrest/dist/cln_rest /release/cln_rest
COPY --from=build /clnrest/dist/clnrest /release/clnrest

ENTRYPOINT ["/clnrest"]
