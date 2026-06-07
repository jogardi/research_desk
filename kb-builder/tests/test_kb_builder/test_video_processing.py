import unittest
from unittest.mock import Mock, patch, MagicMock
from kb_builder.pre_processor.video_file_processor import process_video
from kb_builder.pre_processor.video_block import VideoBlock, VideoRegion

class TestVideoProcessing(unittest.TestCase):

    @patch('kb_builder.pre_processor.video_file_processor.whisper')
    @patch('kb_builder.pre_processor.video_file_processor.VideoFileClip')
    @patch('kb_builder.pre_processor.video_file_processor.os.path.exists')
    @patch('kb_builder.pre_processor.video_file_processor.os.remove')
    def test_process_video_with_timestamps(self, mock_remove, mock_exists, mock_video_clip, mock_whisper):
        # Mock video file and audio extraction
        mock_video = Mock()
        mock_video.duration = 120.0  # 2 minute video
        mock_audio = Mock()
        mock_audio.write_audiofile = Mock()
        mock_video.audio = mock_audio
        mock_video_clip.return_value = mock_video
        
        # Mock file operations
        mock_exists.return_value = True
        
        # Mock whisper model and transcription with segments
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription result with word timestamps
        mock_transcription = {
            'text': 'This is a test transcript. It has multiple sentences.',
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.5,
                    'text': ' This is a test transcript.'
                },
                {
                    'start': 3.5,
                    'end': 6.2,
                    'text': ' It has multiple sentences.'
                }
            ]
        }
        mock_model.transcribe.return_value = mock_transcription
        
        # Process video
        video_file_path = '/test/video.mp4'
        work_folder = '/test/work'
        blocks = process_video(video_file_path, work_folder)
        
        # Verify whisper was called with word_timestamps=True
        mock_model.transcribe.assert_called_once()
        call_args = mock_model.transcribe.call_args
        self.assertEqual(call_args[1].get('word_timestamps'), True)
        
        # Verify blocks were created correctly
        self.assertEqual(len(blocks), 2)
        
        # Check first block
        block1 = blocks[0]
        self.assertIsInstance(block1, VideoBlock)
        self.assertEqual(block1.text, 'This is a test transcript.')
        self.assertEqual(block1.type, 'transcript')
        self.assertIsInstance(block1.region, VideoRegion)
        self.assertEqual(block1.region.start_time, 0.0)
        self.assertEqual(block1.region.end_time, 3.5)
        
        # Check second block
        block2 = blocks[1]
        self.assertEqual(block2.text, 'It has multiple sentences.')
        self.assertEqual(block2.region.start_time, 3.5)
        self.assertEqual(block2.region.end_time, 6.2)
        
    @patch('kb_builder.pre_processor.video_file_processor.whisper')
    @patch('kb_builder.pre_processor.video_file_processor.VideoFileClip')
    @patch('kb_builder.pre_processor.video_file_processor.os.path.exists')
    @patch('kb_builder.pre_processor.video_file_processor.os.remove')
    def test_process_video_fallback_no_segments(self, mock_remove, mock_exists, mock_video_clip, mock_whisper):
        # Mock video file
        mock_video = Mock()
        mock_video.duration = 60.0
        mock_audio = Mock()
        mock_audio.write_audiofile = Mock()
        mock_video.audio = mock_audio
        mock_video_clip.return_value = mock_video
        
        mock_exists.return_value = True
        
        # Mock whisper model and transcription without segments
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription result without segments (fallback case)
        mock_transcription = {
            'text': 'This is a complete transcript without segments.'
        }
        mock_model.transcribe.return_value = mock_transcription
        
        # Process video
        blocks = process_video('/test/video.mp4', '/test/work')
        
        # Verify fallback behavior
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block.text, 'This is a complete transcript without segments.')
        self.assertEqual(block.region.start_time, 0.0)
        self.assertEqual(block.region.end_time, 60.0)  # Should use video duration

if __name__ == '__main__':
    unittest.main() 