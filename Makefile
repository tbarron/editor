clean:
	rm -rf tests/__pycache__
	find . -name "*.pyc" | xargs rm
	find . -name "*~" | xargs rm
