from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import edge_tts
import edge_tts.exceptions
import ffmpeg

from domain.artifacts.speech_artifact import SpeechArtifact
from domain.constants import SPEECH_DIR
from domain.ports.speech_synthesizer import SpeechSynthesizer
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact

log = get_logger()

_SAMPLE_RATE = 24000


class SpeechSynthesisError(Exception):
    """Raised when speech synthesis fails."""


class EdgeTTSSynthesizer(SpeechSynthesizer):
    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        output_dir: Path = SPEECH_DIR,
    ) -> None:
        self._voice = voice
        self._rate = rate
        self._pitch = pitch
        self._volume = volume
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self,
        transcript: LocalizedTranscriptArtifact,
    ) -> SpeechArtifact:
        try:
            return self._do_synthesize(transcript)
        except SpeechSynthesisError:
            raise
        except Exception as exc:
            raise SpeechSynthesisError(f"Speech synthesis failed: {exc}") from exc

    def _do_synthesize(
        self,
        transcript: LocalizedTranscriptArtifact,
    ) -> SpeechArtifact:
        stem = transcript.path.stem
        output_path = self._output_dir / f"{stem}.wav"

        if output_path.exists():
            return SpeechArtifact(path=output_path)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            timeline: list[Path] = []

            cursor = 0.0

            for index, segment in enumerate(transcript.segments):
                silence_needed = segment.start - cursor

                if silence_needed > 0:
                    silence_path = tmp_path / f"silence_{index:06d}.wav"
                    self._generate_silence(silence_needed, silence_path)
                    timeline.append(silence_path)

                mp3_path = tmp_path / f"{index:06d}.mp3"
                wav_path = tmp_path / f"{index:06d}.wav"

                log.info(
                    "speech_synthesis.segment",
                    index=index,
                    total=len(transcript.segments),
                    text=segment.localized_text[:50],
                )

                text = segment.localized_text.strip()
                if not text:
                    silence_path = tmp_path / f"empty_{index:06d}.wav"
                    self._generate_silence(segment.end - segment.start, silence_path)
                    timeline.append(silence_path)
                    cursor = segment.end
                else:
                    self._synthesize_segment(text, mp3_path)
                    self._convert_to_wav(mp3_path, wav_path)
                    timeline.append(wav_path)
                    duration = self._get_duration(wav_path)
                    cursor = segment.start + duration

            if not timeline:
                self._generate_silence(0.0, output_path)
            else:
                self._concatenate(timeline, output_path)

        log.info("speech_synthesis.done", output=str(output_path))
        return SpeechArtifact(path=output_path)

    def _synthesize_segment(self, text: str, output_path: Path) -> None:
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(
                    text,
                    voice=self._voice,
                    rate=self._rate,
                    pitch=self._pitch,
                    volume=self._volume,
                )
                communicate.save_sync(str(output_path))
                return
            except edge_tts.exceptions.EdgeTTSException as exc:
                last_exc = exc
                if attempt < 2:
                    log.warning("speech_synthesis.retry", attempt=attempt + 1, error=str(exc))
        raise SpeechSynthesisError(f"Edge-TTS failed after 3 attempts: {last_exc}") from last_exc

    def _convert_to_wav(self, mp3_path: Path, wav_path: Path) -> None:
        try:
            (
                ffmpeg.input(str(mp3_path))
                .output(str(wav_path), acodec="pcm_s16le", ar=_SAMPLE_RATE, ac=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else str(exc)
            raise SpeechSynthesisError(f"FFmpeg conversion failed: {stderr}") from exc

    def _get_duration(self, wav_path: Path) -> float:
        try:
            probe = ffmpeg.probe(str(wav_path))
            return float(probe["streams"][0]["duration"])
        except (ffmpeg.Error, KeyError, ValueError) as exc:
            raise SpeechSynthesisError(f"Failed to probe audio duration: {exc}") from exc

    def _generate_silence(self, duration: float, output_path: Path) -> None:
        try:
            (
                ffmpeg.input(
                    f"anullsrc=r={_SAMPLE_RATE}:cl=mono",
                    f="lavfi",
                )
                .output(
                    str(output_path),
                    t=f"{duration:.3f}",
                    acodec="pcm_s16le",
                    ar=_SAMPLE_RATE,
                    ac=1,
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else str(exc)
            raise SpeechSynthesisError(f"FFmpeg silence generation failed: {stderr}") from exc

    def _concatenate(self, wav_segments: list[Path], output_path: Path) -> None:
        if len(wav_segments) == 1:
            self._copy_file(wav_segments[0], output_path)
            return

        concat_list = output_path.parent / f"{output_path.stem}_concat.txt"
        try:
            lines = [f"file '{seg.resolve()}'" for seg in wav_segments]
            concat_list.write_text("\n".join(lines))
            (
                ffmpeg.input(str(concat_list), format="concat", safe=0)
                .output(str(output_path), acodec="pcm_s16le", ar=_SAMPLE_RATE)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else str(exc)
            raise SpeechSynthesisError(f"FFmpeg concatenation failed: {stderr}") from exc
        finally:
            concat_list.unlink(missing_ok=True)

    def _copy_file(self, src: Path, dst: Path) -> None:
        try:
            (
                ffmpeg.input(str(src))
                .output(str(dst), acodec="pcm_s16le", ar=_SAMPLE_RATE)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else str(exc)
            raise SpeechSynthesisError(f"FFmpeg copy failed: {stderr}") from exc
