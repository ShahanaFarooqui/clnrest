FROM python:3.8 AS build

WORKDIR /clnrest

COPY . /clnrest

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install pyinstaller && \
    pyinstaller --onefile --distpath ./release cln_rest.py && \
    pyinstaller --onefile --distpath ./release clnrest.py

FROM scratch AS export-stage

COPY --from=build /clnrest/release/cln_rest /release/cln_rest
COPY --from=build /clnrest/release/clnrest /release/clnrest

ENTRYPOINT ["/clnrest"]
