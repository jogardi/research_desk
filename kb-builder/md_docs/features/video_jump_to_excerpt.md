In the UI, in the search results there is a option to "View Excerpt on Source Page" for any given search result. That means you can jump to the position in the pdf where that search result came from and the pdf block with that excerpt is highlighted. 

Some of the search results come from transcribed video. Right now there is no "View Excerpt on Source Page" option in that case. I want to make the same feature work for video. We are already showing the video in the UI when the user clicks "View source document" for a
search result from a video. I want the "View Excerpt on Source Page" to similarly display the video but also jump to the time of that excerpt. whisper.transcribe can return timestamps if you pass word_timestamps=True

The region column for the chunks from the video is currently containing some dummy value. 
It needs to contain the time range for that chunk. Define a new dataclass analgous pdf_block.PdfRegion for the time stamp range. Also, define a new class analagous to pdf_block.PDFBlock. 
Right now video processor is using PDFBlock but that feels wrong. 

We should not use agentic chunking for the video transcript. split_text_by_sentence_and_tokens should use hpc().sentence_splitter for chunking video transcript 
even when hpc()enable_agentic_chunking is true. 

## Implementation Status

**KB Builder Implementation: ✅ COMPLETE**

The KB builder part has been implemented with the following changes:
- Created `VideoRegion` and `VideoBlock` dataclasses
- Updated video processor to use whisper with `word_timestamps=True`
- Video blocks now contain timestamp ranges in the region field
- Video transcripts skip agentic chunking and always use sentence splitting
- Region data is stored as JSON with `start_time` and `end_time` fields

See `md_docs/implementation/video_timestamps_implementation.md` for full details.
