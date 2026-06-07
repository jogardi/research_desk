# updated shared
poetry env list
poetry env remove  ??
poetry install

# re-compile
poetry cache clear _default_cache --all
poetry cache clear PyPI --all
poetry lock --no-update
poetry install

# ntlk
poetry run python -m nltk.downloader -d ~/nltk_data punkt punkt_tab averaged_perceptron_tagger wordnet

# run
cd src/kb_builder
poetry run python process_main.py --profile dev --param1 avalon --param2 stagingsubfolder1
poetry run python title_chunks_process_main.py --profile dev --param1 2012 --param2 override
PYTORCH_ENABLE_MPS_FALLBACK=1 poetry run python process_main.py --profile default --param1 demo --param2 batch1

# execute test cases
poetry run pytest (use -s parameter to see print and log)
poetry run pytest -s -p no:warnings to suppress warnings
--log-cli-level=DEBUG
tests/test_kb_builder/test_chunk.py::TestTextSplitting::test_chunk_by_max_tokens_round_trip (execute specific test case)

# Note
Build the category filename vector database as as separate process instead of incorporating it into the main process for performance and robustness
There is not much gain in adding more and more filenames to this vector db -- but would have to re-execute for a new category
So right now it is a manual process to run this program periodically
Must run after adding a new category

create TABLE CATEGORY (
ID integer primary key,
CATEGORY varchar(1024))

insert into CATEGORY (CATEGORY) select distinct CATEGORY from DOCUMENT


# ToDo
for recovery, there is no simple way to remove items from hnswlib, so we may end up with orphaned items
need process to cleanup these orphans
there will need to be error handling in webservice so that if there is a semantic search match, but no chunks or document, to remove these matches from search results

note that the chunks are not commited to the sqlite database until the vector db has added the indexes -- so maybe this cannot happen

When a file fails in a folder, the process does not continue for that folder, it goes to the next one

kb_artifact.py change all functions to throw E instead of true/false

# General
If the files are in a folder where there are other folders -- then create a vector db named category_general

# *** Must run this command so it works with the GPU ***
poetry run pip install torch --index-url https://download.pytorch.org/whl/mps
