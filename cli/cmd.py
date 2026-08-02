import json
import os
import shutil
from pathlib import Path

import typer

from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact, LocalizedTranscriptSegment
from domain.artifacts.url import YoutubeURL
from domain.constants import ARTIFACTS_ROOT
from pipeline.cons import Pipeline
from providers.edge_tts.synthesizer import EdgeTTSSynthesizer
from providers.ffmpeg.extractor import FFmpegAudioExtractor
from providers.ffmpeg.muxer import FFmpegVideoMuxer
from providers.groq.transcriber import GroqTranscriber
from providers.groq.translator import GroqTranslator
from providers.yt_downloader import YtDlpDownloader
from stages.audio_extraction_stage import AudioExtractionStage
from stages.download_stage import DownloadStage
from stages.mux_stage import MuxStage
from stages.speech_synthesis_stage import SpeechSynthesisStage
from stages.transcription_stage import TranscriptionStage
from stages.translation_stage import TranslationStage
from utils.logging import get_logger

log = get_logger()


def register(app: typer.Typer) -> None:
    app.command()(dub)
    app.command()(synthesize)
    app.command()(clean)
    app.command()(version)


def dub(
    url: str = typer.Argument(help="YouTube video URL"),
    voice: str = typer.Option("female", help="Voice gender: male or female"),
) -> None:
    log.info("pipeline.start", url=url)

    voice_name = "en-US-GuyNeural" if voice == "male" else "en-US-AriaNeural"

    pipeline = Pipeline()
    mux_stage = MuxStage(FFmpegVideoMuxer(), pipeline.state)

    sequence = (
        pipeline.add(DownloadStage(YtDlpDownloader()))
        .add(AudioExtractionStage(FFmpegAudioExtractor()))
        .add(TranscriptionStage(GroqTranscriber(api_key=os.getenv("GROQ_API_KEY"))))
        .add(TranslationStage(GroqTranslator(api_key=os.getenv("GROQ_API_KEY"))))
        .add(SpeechSynthesisStage(EdgeTTSSynthesizer(voice=voice_name)))
        .add(mux_stage)
    )

    yt_url = None
    try:
        yt_url = YoutubeURL.model_validate({"value": url})
    except Exception:
        log.error("url.invalid", url=url)
        return

    sequence.run(yt_url)

    log.info("pipeline.done", url=url)


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
            id=s["id"],
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

    pipeline = Pipeline().add(
        SpeechSynthesisStage(EdgeTTSSynthesizer()),
    )
    pipeline.run(artifact)

    log.info("synthesize.done", transcript=transcript_path)


def version() -> None:
    typer.echo("vubber 0.1.0")


def clean(url: str | None = typer.Argument(default=None, help="YouTube video URL to clean artifacts for")) -> None:
    if url is None:
        if ARTIFACTS_ROOT.exists():
            shutil.rmtree(ARTIFACTS_ROOT)
            log.info("clean.done", scope="all")
        else:
            log.info("clean.nothing")
        return

    yt_url = None
    try:
        yt_url = YoutubeURL.model_validate({"value": url})
    except Exception as exc:
        log.error("url.invalid", url=url)
        raise typer.Exit(code=1) from exc

    video_id = yt_url.video_id
    deleted = 0

    for directory in ARTIFACTS_ROOT.iterdir():
        if not directory.is_dir():
            continue
        for file in directory.iterdir():
            if video_id in file.stem:
                file.unlink()
                deleted += 1

    transcript_json = ARTIFACTS_ROOT.joinpath("transcripts", f"{video_id}.json")
    if transcript_json.exists():
        raw = json.loads(transcript_json.read_text())
        language = raw.get("language", "")
        if language:
            localized = ARTIFACTS_ROOT.joinpath(
                "localized",
                f"{language}_English.json",
            )
            speech = ARTIFACTS_ROOT.joinpath("speech", f"{language}_English.wav")
            for f in (localized, speech):
                if f.exists():
                    f.unlink()
                    deleted += 1

    log.info("clean.done", video_id=video_id, files=deleted)
