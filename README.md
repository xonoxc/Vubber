# vubber

YouTube video dubbing pipeline.

## Installation

```bash
uv sync
```

## Usage

```bash
vubber dub <youtube-url>
```

## Development

```bash
uv sync
uv run ruff check src tests
uv run ruff format src tests
uv run pyright
uv run pytest
```
