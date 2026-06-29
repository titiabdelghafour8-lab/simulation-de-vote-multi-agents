.PHONY: all build simulate dashboard clean

VENV = linux_venv
PYTHON = $(VENV)/bin/python
STREAMLIT = $(VENV)/bin/streamlit

all: build

build:
	chmod +x build.sh
	./build.sh

simulate:
	$(PYTHON) simulation.py

dashboard:
	$(STREAMLIT) run dashboard.py

clean:
	rm -rf $(VENV) linux_venv __pycache__
