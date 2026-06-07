import os
import whisper
from shared.logger import Logger  
from moviepy.editor import VideoFileClip
from kb_builder.pre_processor.video_block import VideoBlock, VideoRegion
from typing import List

def process_video(video_file_path: str, work_folder: str) -> List[VideoBlock]:
    #file paths
    base_name = os.path.basename(video_file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    video = VideoFileClip(video_file_path)
    audio_file_path = work_folder + '/' + file_name_without_ext + '.wav'

    # Extract the audio from the video
    video.audio.write_audiofile(audio_file_path, verbose=False, logger=None)

    # Transcribe the audio with word timestamps
    model = whisper.load_model("base") 
    result = model.transcribe(audio_file_path, word_timestamps=True)
    
    # clean up
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
    
    blocks = []
    
    # Process segments from whisper to create VideoBlocks
    if 'segments' in result:
        for segment in result['segments']:
            # Each segment has 'start', 'end', and 'text' fields
            start_time = segment.get('start', 0.0)
            end_time = segment.get('end', 0.0)
            text = segment.get('text', '').strip()
            
            if text:  # Only create blocks for non-empty text
                region = VideoRegion(start_time=start_time, end_time=end_time)
                block = VideoBlock(text=text, type="transcript", region=region)
                blocks.append(block)
    else:
        # Fallback if segments are not available - create a single block
        # with the full transcript and no time information
        if result.get("text"):
            region = VideoRegion(start_time=0.0, end_time=video.duration if video.duration else 0.0)
            block = VideoBlock(text=result["text"], type="transcript", region=region)
            blocks.append(block)
    
    return blocks

