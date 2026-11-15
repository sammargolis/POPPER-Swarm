.PHONY: install test benchmark dashboard figures slides clean

install:
	pip install -r requirements.txt
	pip install -e .

test:
	PYTHONPATH=src:. pytest -q

benchmark:
	PYTHONPATH=src:. bash benchmark_scripts/run_bixbench3.sh

dashboard:
	PYTHONPATH=src:. uvicorn popper_swarm.dashboard:app --host 127.0.0.1 --port 8765

figures:
	PYTHONPATH=src:. python3 scripts/build_repo_figures.py

slides:
	PYTHONPATH=src:. python3 scripts/build_presentation.py

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
