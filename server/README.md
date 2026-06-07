poetry env list
poetry env info

poetry install
poetry shell
poetry env list

poetry env remove webservice-Ti2iXNF3-py3.10
cd src/webservice
poetry run python server_main.py

#gunicorn
poetry run gunicorn -c gunicorn_config.py  > gunicorn_output.log 2> gunicorn_error.log


# run
cd src/webservice
poetry run python server_main.py --profile default

# re-compile
poetry cache clear _default_cache --all
poetry cache clear PyPI --all
poetry lock --no-update
poetry install

# execute test cases
poetry run pytest (use -s parameter to see print and log)
poetry run pytest -s tests/webservice/persistence/test_research_desk_prompt_backendless.py::TestResearchDeskPromptBackendless::test_add_prompt_happy (execute specific test case)

poetry run pytest tests/webservice/search/test_search.py::TestSearch::test_fts_search_happy

# after modifying shared
poetry env remove webservice--oiGeYvP-py3.10
poetry install

# Poetry virtual env path:
poetry env info --path

# Down loading NLTK data (for nouns.py)
poetry run python -m nltk.downloader -d ~/.nltk_data punkt averaged_perceptron_tagger wordnet
# if still get error, try this:
poetry run python -c "import nltk; nltk.download('punkt')"

# Down loading SpaCy data (for semantic_nouns.py)
poetry run python -m spacy download en_core_web_sm 

## Virtual env location:
~/.cache/pypoetry/virtualenvs

## Deploy to Cloud
Go to research desk folder
npm run build
Copy from the rd dist folder into the webservice static folder

--install cpu ony torch
poetry env info
source "$(poetry env info --path)/bin/activate"
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cpu

poetry run python server_main.py --profile demo
