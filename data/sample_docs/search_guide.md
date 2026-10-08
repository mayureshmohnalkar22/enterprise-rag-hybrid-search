# Search and Indexing Guide

## Indexing
Uploaded documents are parsed and divided into overlapping chunks. Every chunk retains source filename, page number, version hash and chunk index. Updated documents replace their previous indexed versions.

## Vector search
Dense retrieval compares a query embedding against normalized chunk embeddings using cosine similarity. The dense index retrieves semantic matches even when the query and document use different vocabulary.

## Keyword search
Sparse retrieval uses BM25 to rank chunks containing exact keywords, function names, configuration keys and error codes. Keyword retrieval complements semantic similarity.

## Hybrid fusion
Reciprocal Rank Fusion combines dense and sparse ranked lists using scores of weight divided by sixty plus rank. A configurable dense weight controls the contribution of vector retrieval. The fusion layer deduplicates chunks by stable chunk ID.

## Citation policy
Answers must cite numbered source excerpts using square brackets. A citation reference must correspond to a retrieved chunk. Citation presence alone does not prove a claim is factually supported by its source.
