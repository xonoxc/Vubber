import os

import typer
from dotenv import load_dotenv

from domain.artifacts.url import YoutubeURL
from pipeline.cons import Pipeline
from providers.faster_whisper.transcriber import FasterWhisperTranscriber
from providers.ffmpeg.extractor import FFmpegAudioExtractor
from providers.groq.translator import GroqTranslator
from providers.yt_downloader import YtDlpDownloader
from stages.audio_extraction_stage import AudioExtractionStage
from stages.download_stage import DownloadStage
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
def version() -> None:
    # Show version information.
    typer.echo("vubber 0.1.0")
