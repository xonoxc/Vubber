import json
import os
from pathlib import Path

import typer
from dotenv import load_dotenv

from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact, LocalizedTranscriptSegment
from domain.artifacts.url import YoutubeURL
from pipeline.cons import Pipeline
from providers.edge_tts.synthesizer import EdgeTTSSynthesizer
from providers.faster_whisper.transcriber import FasterWhisperTranscriber
from providers.ffmpeg.extractor import FFmpegAudioExtractor
from providers.groq.translator import GroqTranslator
from providers.yt_downloader import YtDlpDownloader
from stages.audio_extraction_stage import AudioExtractionStage
from stages.download_stage import DownloadStage
from stages.speech_synthesis_stage import SpeechSynthesisStage
from stages.transcription_stage import TranscriptionStage
from stages.translation_stage import TranslationStage
from utils.logging import configure_logging, get_logger

load_dotenv()
configure_logging()
log = get_logger()

app = typer.Typer(name="vubber", help="YouTube video dubbing pipeline")


@app.command()
def dub(url: str = typer.Argument(help="YouTube video URL")) -> None:
    # Download, transcribe, translate, and dub a YouTube video

    log.info("pipeline.start", url=url)

    sequence = (
        Pipeline()
        .add(DownloadStage(YtDlpDownloader()))
        .add(AudioExtractionStage(FFmpegAudioExtractor()))
        .add(TranscriptionStage(FasterWhisperTranscriber()))
        .add(TranslationStage(GroqTranslator(api_key=os.getenv("GROQ_API_KEY"))))
        .add(SpeechSynthesisStage(EdgeTTSSynthesizer()))
    )

    yt_url = None
    try:
        yt_url = YoutubeURL.model_validate({"value": url})
    except Exception:
        log.error("url.invalid", url=url)
        return

    sequence.run(yt_url)

    log.info("pipeline.done", url=url)


@app.command()
def synthesize(
    transcript_path: str = typer.Argument(help="Path to a localized transcript JSON file"),
) -> None:
    log.info("synthesize.start", transcript=transcript_path)

    path = Path(transcript_path)
    if not path.exists():
        log.error("synthesize.file_not_found", path=transcript_path)
        raise typer.Exit(code=1)

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        log.error("synthesize.invalid_json", path=transcript_path)
        raise typer.Exit(code=1) from exc

    segments = [
        LocalizedTranscriptSegment(
            start=s["start"],
            end=s["end"],
            original_text=s["original_text"],
            localized_text=s["localized_text"],
        )
        for s in raw["segments"]
    ]

    artifact = LocalizedTranscriptArtifact(
        path=path,
        source_language=raw["source_language"],
        target_language=raw["target_language"],
        segments=segments,
    )

    pipeline = Pipeline().add(SpeechSynthesisStage(EdgeTTSSynthesizer()))
    pipeline.run(artifact)

    log.info("synthesize.done", transcript=transcript_path)


@app.command()
def version() -> None:
    # Show version information.
    typer.echo("vubber 0.1.0")
