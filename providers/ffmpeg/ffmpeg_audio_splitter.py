from pathlib import Path

import ffmpeg

from config.constants import AUDIO_SPEECH_VOICE_SEGMENTS_PATH
from domain.artifacts.audio_artifact import AudioArtifact
from domain.ports.audio_splitter import AudioSplitter
from providers.vad.vad_provider import SpeechReigon


class FFempegAudioSplitter(AudioSplitter):
    def split(
        self,
        audio: AudioArtifact,
        speech_reigons: list[SpeechReigon],
    ) -> Path:
        output_dir_path = AUDIO_SPEECH_VOICE_SEGMENTS_PATH.joinpath(
            audio.path.stem,
        )
        output_dir_path.mkdir(parents=True, exist_ok=True)

        for idx, path in enumerate(speech_reigons):
            output_path = output_dir_path.joinpath(f"{audio.path.stem}_{idx}.wav")
            self.extract_segment(
                audio.path,
                path,
                output_path,
            )

        return output_dir_path

    def extract_segment(
        self,
        audio: Path,
        region: SpeechReigon,
        output: Path,
    ) -> None:
        start, end = region

        (
            ffmpeg.input(str(audio), ss=start, to=end)
            .output(
                str(output),
                acodec="pcm_s16le",
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
