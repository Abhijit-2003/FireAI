.PHONY: install test run-all run-a run-b clean

install:
	pip install -r requirements.txt

test:
	python -m pytest project_a/tests/ project_b/tests/ -v

run-a:
	@echo "=== Project A: Income Tax Engine ==="
	@echo "--- Running Test Suite ---"
	python -m pytest project_a/tests/ -v --tb=short
	@echo "--- Running Benchmarks ---"
	python -m project_a.benchmarks

run-b:
	@echo "=== Project B: Data Quality Checks ==="
	@echo "--- Profiling Raw Data ---"
	python -m project_b.data.profile
	@echo "--- Running Detectors ---"
	python -m pytest project_b/tests/ -v --tb=short
	@echo "--- Running Benchmarks ---"
	python -m project_b.benchmarks

run-all: run-a run-b
	@echo ""
	@echo "=== All results reproduced successfully ==="

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

