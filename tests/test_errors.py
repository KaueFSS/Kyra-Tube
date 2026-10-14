import pytest

from core.errors import explain, short_reason

# Textos reais (ou muito próximos) do que o yt-dlp devolve.
CASES = [
    ("ERROR: [youtube] abc123: Sign in to confirm you’re not a bot. Use --cookies-from-browser", "bot_check"),
    ("ERROR: [youtube] abc123: Sign in to confirm you're not a bot", "bot_check"),
    ("ERROR: unable to download video data: HTTP Error 429: Too Many Requests", "rate_limit"),
    ("ERROR: unable to download video data: HTTP Error 403: Forbidden", "forbidden"),
    ("ERROR: [youtube] abc123: Private video. Sign in if you've been granted access to this video", "private"),
    ("ERROR: [youtube] abc123: Join this channel to get access to members-only content", "members"),
    ("ERROR: [youtube] abc123: Sign in to confirm your age. This video may be inappropriate for some users", "age"),
    ("ERROR: [youtube] abc123: This video contains content from Sony, who has blocked it on copyright grounds", "copyright"),
    ("ERROR: [youtube] abc123: The uploader has not made this video available in your country", "geo"),
    ("ERROR: [youtube] abc123: Premieres in 3 hours", "upcoming"),
    ("ERROR: [youtube] abc123: Video unavailable", "unavailable"),
    ("ERROR: [youtube] abc123: This video has been removed by the uploader", "unavailable"),
    ("ERROR: [generic] 'abc' is not a valid URL", "bad_url"),
    ("ERROR: Unsupported URL: https://example.com/x", "bad_url"),
    ("ERROR: [youtube] abc123: Unable to download webpage: <urlopen error [Errno 11001] getaddrinfo failed>", "network"),
    ("ERROR: Requested format is not available. Use --list-formats for a list of available formats", "format"),
    ("ERROR: Postprocessing: ffprobe and ffmpeg not found", "ffmpeg"),
    ("OSError: [Errno 28] No space left on device", "disk"),
    ("PermissionError: [Errno 13] Permission denied: 'C:\\\\x.mp4'", "disk"),
    ("algo que ninguém previu", "unknown"),
]


@pytest.mark.parametrize("raw,key", CASES)
def test_each_error_gets_the_right_explanation(raw, key):
    assert explain(raw).key == key


def test_every_problem_says_what_to_try():
    for _raw, key in CASES:
        problem = explain(_raw)
        assert problem.title and problem.message and len(problem.tips) >= 1, key


def test_the_internet_blocks_mention_restarting_the_router():
    # O caso que o próprio autor resolveu reiniciando a internet.
    for raw in ("Sign in to confirm you're not a bot", "HTTP Error 429: Too Many Requests"):
        assert any("roteador" in tip for tip in explain(raw).tips)


def test_short_reason_drops_the_prefix_and_color_codes():
    assert short_reason("\x1b[0;31mERROR:\x1b[0m [youtube] x: Video unavailable\nmais coisas") == "[youtube] x: Video unavailable"
    assert short_reason(None) == ""
