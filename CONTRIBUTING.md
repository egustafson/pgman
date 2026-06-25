# Contributing

Thank you for your interest in contributing to pgman!

## Development Setup

1. Clone the repository.
2. Install [uv](https://docs.astral.sh/uv/).
3. Install all dependencies (including dev tools):
   ```sh
   uv sync --dev
   ```

## Running Tests

```sh
uv run pytest
```

To include coverage:
```sh
uv run pytest --cov=pgman
```

## Code Quality

pgman uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```sh
uv run ruff check .          # lint
uv run ruff format .         # format
uv run ruff format --check . # check formatting without modifying files
```

## Submitting Changes

1. Fork the repository and create a feature branch from `main`.
2. Make your changes, adding or updating tests as appropriate.
3. Ensure all tests pass and the code passes lint and format checks.
4. Open a pull request with a clear description of your changes and the motivation behind them.
