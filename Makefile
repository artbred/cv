.PHONY: rebuild
rebuild:
	docker builder prune -f
	docker-compose build --force-rm --no-cache


.PHONY: up
up: rebuild
	docker-compose up -d --remove-orphans


# Initalize embeddings in redis, call "make populate FLUSH=-f" to force delete all data and reset index
.PHONY: populate
populate:
	docker-compose exec app python3 populate.py $(FLUSH)


.PHONY: convert
convert:
	cd analytics && jupytext --to py data.ipynb
	# cd analytics && jupyter nbconvert --to python --TemplateExporter.exclude_input_prompt=True --TemplateExporter.exclude_output_prompt=True --TemplateExporter.exclude_markdown=True data.ipynb 

.PHONY: collect
collect:
	docker-compose exec analytics python3 data.py