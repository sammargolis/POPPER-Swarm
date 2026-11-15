.PHONY: install test benchmark dashboard figures slides clean

install:
	pip install -e ".[dev,figures]"

test:
	pytest -q

benchmark:
	bash benchmark_scripts/run_bixbench3.sh

dashboard:
	uvicorn popper_swarm.dashboard:app --host 127.0.0.1 --port 8765

figures:
	python3 scripts/build_repo_figures.py

slides:
	python3 scripts/build_presentation.py

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
