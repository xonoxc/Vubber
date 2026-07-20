import typer

from domain.artifacts.url import YoutubeURL
from pipeline.cons import Pipeline
from providers.faster_whisper.transcriber import FasterWhisperTranscriber
from providers.ffmpeg.extractor import FFmpegAudioExtractor
from providers.yt_downloader import YtDlpDownloader
from stages.audio_extraction_stage import AudioExtractionStage
from stages.download_stage import DownloadStage
from stages.transcription_stage import TranscriptionStage

app = typer.Typer(name="vubber", help="YouTube video dubbing pipeline")


@app.command()
def dub(url: str = typer.Argument(help="YouTube video URL")) -> None:
    # Download, transcribe, translate, and dub a YouTube video

    sequence = (
        Pipeline()
        .add(DownloadStage(YtDlpDownloader()))
        .add(AudioExtractionStage(FFmpegAudioExtractor()))
        .add(TranscriptionStage(FasterWhisperTranscriber()))
    )

    yt_url = None
    try:
        yt_url = YoutubeURL.model_validate({"value": url})
    except Exception:
        print("Invalid youtube url please enter a valid one.")
        return

    sequence.run(yt_url)

    typer.echo(f"Processing: {url}")


@app.command()
def version() -> None:
    # Show version information.
    typer.echo("vubber 0.1.0")
