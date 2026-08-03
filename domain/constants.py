from pathlib import Path

# output artifacts related paths
ARTIFACTS_ROOT = Path("artifacts")

VIDEOS_DIR = ARTIFACTS_ROOT.joinpath("videos")


AUDIO_DIR = ARTIFACTS_ROOT.joinpath("audio")

TRANSCRIPTS_DIR = ARTIFACTS_ROOT.joinpath("transcripts")


LOCALIZED_DIR = ARTIFACTS_ROOT.joinpath("localized")


SPEECH_DIR = ARTIFACTS_ROOT.joinpath("speech")


OUTPUT_DIR = ARTIFACTS_ROOT.joinpath("output")


# helper to create system prompt path
def create_system_prompt_path(prompt_name: str) -> Path:
    return (
        Path(__file__)
        .resolve()
        .parent.joinpath(
            "system_prompts",
            f"{prompt_name}.xml",
        )
    )


# translation related config
TRANSLATION_PROMPT = create_system_prompt_path("translation")
TRANSLATION_RETRY_PROMPT = create_system_prompt_path("translation_retry")

TRANSLATiON_BATCH_SIZE = 20

TRANSLATION_MAX_RETRIES = 3

TRANSLATION_RATE_LIMIT_MAX_RETRIES = 5

TRANSLATION_RATE_LIMIT_MAX_DELAY_SECONDS = 300
