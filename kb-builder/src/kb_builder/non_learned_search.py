from functools import lru_cache
@lru_cache()
def lucene_analyzer():
    from pyserini.analysis import Analyzer, get_lucene_analyzer
    return Analyzer(get_lucene_analyzer(stemming=False))

class NonLearnedSearch:
    @lru_cache()
    def __init__(self):
        from pyserini.index.lucene import LuceneIndexer
        from jnius import autoclass

        # Import LogManager and Level from Log4j
        LogManager = autoclass('org.apache.logging.log4j.LogManager')
        Level = autoclass('org.apache.logging.log4j.Level')
        Configurator = autoclass('org.apache.logging.log4j.core.config.Configurator')

        # Get the root logger
        logger = LogManager.getRootLogger()

        # Set the log level (e.g., INFO, WARN, ERROR, DEBUG, TRACE)
        Configurator.setLevel(logger, Level.WARN)


    def add_batch_dict(self, path, for_lucene):
        from pyserini.index.lucene import LuceneIndexer
        from shared.keyword_search import nltk_remove_stopwords
        import copy
        # deep copy for_lucene
        for_lucene = copy.deepcopy(for_lucene)
        data = []
        for x in for_lucene:
            original_contents = x['contents']
            contents = nltk_remove_stopwords(original_contents)
            if len(contents.strip()) > 0:
                x['contents'] = contents
                data.append(x)
        lucene = LuceneIndexer(path, append=True)
        lucene.add_batch_dict(data)
        lucene.close()
