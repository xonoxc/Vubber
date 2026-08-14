from silero_vad import get_speech_timestamps, load_silero_vad, read_audio

from domain.artifacts.audio_artifact import AudioArtifact
from domain.ports.vad import VADer


class SileroVad(VADer):
    def load_vad_model(self) -> None:
        self.model = load_silero_vad()

    def detect(self, audio: AudioArtifact) -> list[tuple[float, float]]:
        wav = read_audio(str(audio.path))

        speech_timestamps = get_speech_timestamps(
            wav,
            self.model,
            return_seconds=True,
        )

        return [(ts["start"], ts["end"]) for ts in speech_timestamps]
