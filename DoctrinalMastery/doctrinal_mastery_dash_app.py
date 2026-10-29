"""Dash page for the Doctrinal Mastery scripture fill-in game."""

import json
import random
import re

from dash import ALL, Input, Output, State, ctx, dcc, html

PREFIX = "dm"
STOPWORDS = {
    "a", "after", "all", "am", "an", "and", "any", "as", "at", "be", "because", "been",
    "before", "being", "between", "but", "by", "called", "can", "continue", "curse",
    "did", "do", "does", "for", "from", "gave", "give", "given", "had", "has", "have",
    "he", "her", "here", "his", "i", "if", "in", "into", "is", "it", "its", "itself",
    "me", "my", "no", "not", "of", "off", "on", "one", "or", "our", "out", "over",
    "shall", "she", "that", "the", "their", "them", "then", "there", "they", "this",
    "those", "thou", "thy", "to", "too", "unto", "up", "us", "very", "was", "we",
    "were", "what", "when", "where", "which", "who", "why", "will", "with", "would",
    "ye", "you", "your", "yours"
}


def _build_spread_blanks(text, count=10):
    words = []
    seen = set()
    for token in re.findall(r"\b[\w']+\b|[^\w\s]", text):
        cleaned = token.strip(".,;:!?\"“”‘’()[]{}—–")
        if not cleaned or cleaned.isdigit():
            continue
        lowered = cleaned.lower()
        if lowered in STOPWORDS or lowered in seen:
            continue
        seen.add(lowered)
        words.append(cleaned)

    if len(words) <= count:
        return words

    selected = []
    step = len(words) / count
    for idx in range(count):
        position = min(len(words) - 1, int(idx * step + (step / 2)))
        selected.append(words[position])

    result = []
    seen = set()
    for word in selected:
        lowered = word.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(word)

    if len(result) < count:
        for word in words:
            lowered = word.lower()
            if lowered not in seen:
                result.append(word)
                seen.add(lowered)
            if len(result) == count:
                break

    return result[:count]


VERSES = [
    {
        "reference": "Moses 1:39",
        "source": "Pearl of Great Price",
        "text": "For behold, this is my work and my glory—to bring to pass the immortality and eternal life of man.",
        "blanks": [
            "behold",
            "work",
            "glory",
            "bring",
            "pass",
            "immortality",
            "eternal",
            "life",
            "man",
            "this",
        ],
    },
    {
        "reference": "Moses 7:18",
        "source": "Pearl of Great Price",
        "text": "And the Lord called his people Zion, because they were of one heart and one mind, and dwelt in righteousness; and there was no poor among them.",
        "blanks": [
            "Lord",
            "people",
            "Zion",
            "heart",
            "mind",
            "dwelt",
            "righteousness",
            "poor",
            "among",
            "called",
        ],
    },
    {
        "reference": "Abraham 2:9-11",
        "source": "Pearl of Great Price",
        "text": "And I will make of thee a great nation, and I will bless thee above measure, and make thy name great among all nations, and thou shalt be a blessing unto thy seed after thee, that in their hands they shall bear this ministry and Priesthood unto all nations; And I will bless them through thy name; for as many as receive this Gospel shall be called after thy name, and shall be accounted thy seed, and shall rise up and bless thee, as their father; And I will bless them that bless thee, and curse them that curse thee; and in thee (that is, in thy Priesthood) and in thy seed (that is, thy Priesthood), for I give unto thee a promise that this right shall continue in thee, and in thy seed after thee (that is to say, the literal seed, or the seed of the body) shall all the families of the earth be blessed, even with the blessings of the Gospel, which are the blessings of salvation, even of life eternal.",
        "blanks": [
            "make",
            "nation",
            "bless",
            "measure",
            "name",
            "great",
            "seed",
            "Priesthood",
            "receive",
            "promise",
        ],
    },
    {
        "reference": "Abraham 3:22-23",
        "source": "Pearl of Great Price",
        "text": "Now the Lord had shown unto me, Abraham, the intelligences that were organized before the world was; and among all these there were many of the noble and great ones; And God saw these souls that they were good, and he stood in the midst of them, and he said: These I will make my rulers; for he stood among those that were spirits, and he saw that they were good; and he said unto me: Abraham, thou art one of them; thou wast chosen before thou wast born.",
        "blanks": [
            "Lord",
            "showed",
            "organized",
            "world",
            "many",
            "noble",
            "good",
            "midst",
            "rulers",
            "chosen",
        ],
    },
    {
        "reference": "Genesis 1:26-27",
        "source": "Old Testament",
        "text": "And God said, Let us make man in our image, after our likeness: and let them have dominion over the fish of the sea, and over the fowl of the air, and over the cattle, and over all the earth, and over every creeping thing that creepeth upon the earth. So God created man in his own image, in the image of God created he him; male and female created he them.",
        "blanks": [
            "God",
            "make",
            "image",
            "likeness",
            "dominion",
            "earth",
            "creeping",
            "created",
            "male",
            "female",
        ],
    },
    {
        "reference": "Genesis 2:24",
        "source": "Old Testament",
        "text": "Therefore shall a man leave his father and his mother, and shall cleave unto his wife: and they shall be one flesh.",
        "blanks": [
            "man",
            "leave",
            "father",
            "mother",
            "cleave",
            "wife",
            "one",
            "flesh",
            "shall",
            "Therefore",
        ],
    },
]


def _new_game_state():
    return {
        "initialized": True,
        "index": 0,
        "score": 0,
        "submitted": False,
        "answers": [],
        "results": [],
        "placements": {},
    }


def _tokenize(text):
    return re.findall(r"\b[\w']+\b|[^\w\s]", text)


def _render_verse(verse, answer_values=None, submitted=False):
    answer_values = answer_values or [""] * len(verse["blanks"])
    blank_map = {word.lower(): index for index, word in enumerate(verse["blanks"])}
    seen = set()
    tokens = []

    for token in _tokenize(verse["text"]):
        token_lower = token.lower()
        if token_lower in blank_map and token_lower not in seen:
            idx = blank_map[token_lower]
            seen.add(token_lower)
            current_word = answer_values[idx] if len(answer_values) > idx else ""
            tokens.append(
                html.Div(
                    current_word if current_word else "_____",
                    id={"type": f"{PREFIX}-slot", "index": idx},
                    className="dm-slot",
                    draggable="false",
                    **{"data-index": str(idx), "data-word": current_word},
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "minWidth": "120px",
                        "padding": "0.35rem 0.7rem",
                        "margin": "0 0.2rem",
                        "borderRadius": "8px",
                        "border": "2px dashed #0F172A",
                        "backgroundColor": "#FFFFFF",
                        "color": "#111827",
                        "fontWeight": "bold",
                        "minHeight": "42px",
                        "verticalAlign": "middle",
                    },
                )
            )
        else:
            tokens.append(html.Span(token, style={"whiteSpace": "pre-wrap"}))

        if token and token[-1].isalnum():
            tokens.append(html.Span(" ", style={"whiteSpace": "pre-wrap"}))

    shuffled_words = list(verse["blanks"])
    random.shuffle(shuffled_words)

    word_bank = [
        html.Div(
            word,
            key=f"bank-{idx}",
            id={"type": f"{PREFIX}-word", "index": idx, "word": word},
            className="dm-word",
            draggable="true",
            **{"data-index": str(idx), "data-word": word},
            style={
                "padding": "0.6rem 0.9rem",
                "borderRadius": "8px",
                "backgroundColor": "#E0E7FF",
                "border": "1px solid #818CF8",
                "fontWeight": "bold",
                "cursor": "grab",
                "userSelect": "none",
                "textAlign": "center",
                "boxShadow": "0 2px 8px rgba(79,70,229,0.15)",
            },
        )
        for idx, word in enumerate(shuffled_words)
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(verse["reference"], style={"fontWeight": "bold", "fontSize": "1.3rem"}),
                    html.Div(verse["source"], style={"color": "#475569", "fontSize": "0.95rem"}),
                ],
                style={"marginBottom": "1rem"},
            ),
            html.Div(
                [
                    html.Div(
                        tokens,
                        style={
                            "fontSize": "1.3rem",
                            "lineHeight": "2.1",
                            "padding": "1.25rem",
                            "backgroundColor": "#F8FAFC",
                            "border": "1px solid #CBD5E1",
                            "borderRadius": "12px",
                            "whiteSpace": "normal",
                            "flex": "1",
                        },
                    ),
                    html.Div(
                        [
                            html.Div("Word bank", style={"fontWeight": "bold", "marginBottom": "0.7rem"}),
                            html.Div(
                                word_bank,
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(120px, 1fr))",
                                    "gap": "0.6rem",
                                    "padding": "0.75rem",
                                    "backgroundColor": "#EEF2FF",
                                    "borderRadius": "10px",
                                    "border": "1px solid #C7D2FE",
                                },
                            ),
                        ],
                        style={
                            "minWidth": "220px",
                            "maxWidth": "260px",
                            "marginLeft": "1rem",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start", "gap": "1rem"},
            ),
        ]
    )


def _render_game(state):
    if not state or not state.get("initialized"):
        return html.Div("Starting game…")

    if state["index"] >= len(VERSES):
        total_possible = sum(len(verse["blanks"]) for verse in VERSES)
        return html.Div(
            [
                html.H2("🎉 Practice Complete!"),
                html.Div(f"Final score: {state['score']} / {total_possible}", style={"fontSize": "1.5rem", "marginBottom": "1rem"}),
                html.Button("🔁 Start Again", id=f"{PREFIX}-restart", style={"padding": "0.75rem 1rem"}),
            ],
            style={"padding": "1rem", "maxWidth": "900px"},
        )

    verse = VERSES[state["index"]]
    answer_values = state.get("answers", [""] * len(verse["blanks"]))
    correct_answers = [word for word in verse["blanks"]]

    content = [
        html.H3("Doctrinal Mastery Fill-In"),
        html.Div(
            f"Verse {state['index'] + 1} of {len(VERSES)} • Score: {state['score']}",
            style={"marginBottom": "1rem", "fontWeight": "bold", "color": "#1E3A8A"},
        ),
        _render_verse(verse, answer_values, state.get("submitted", False)),
    ]

    if state.get("submitted"):
        correct_count = sum(
            1 for value, expected in zip(answer_values, correct_answers) if value.strip().lower() == expected.lower()
        )
        content.extend(
            [
                html.Div(
                    f"You got {correct_count} out of {len(correct_answers)} correct.",
                    style={
                        "marginTop": "1rem",
                        "padding": "0.8rem 1rem",
                        "backgroundColor": "#DBEAFE",
                        "borderRadius": "8px",
                        "fontWeight": "bold",
                        "color": "#1E3A8A",
                    },
                ),
                html.Div(
                    [
                        html.Strong("Answer key: "),
                        ", ".join(correct_answers),
                    ],
                    style={"marginTop": "0.8rem", "fontSize": "1rem"},
                ),
                html.Button("➡️ Next Verse", id=f"{PREFIX}-next", style={"marginTop": "1rem", "padding": "0.75rem 1rem"}),
            ]
        )
    else:
        content.append(
            html.Button("✅ Check My Answers", id=f"{PREFIX}-submit", style={"marginTop": "1rem", "padding": "0.75rem 1rem"})
        )

    return html.Div(content, style={"maxWidth": "1000px", "padding": "1rem"})


def layout():
    return html.Div(
        [
            dcc.Store(id=f"{PREFIX}-state", storage_type="session", data={}),
            dcc.Store(id=f"{PREFIX}-drag-state", storage_type="memory", data={}),
            html.Div(
                [
                    html.H2("📖 Doctrinal Mastery Practice"),
                    html.P("Fill in the missing nouns and verbs for each scripture. Drag the words into place from the side bank."),
                    html.Button("▶ Start Practice", id=f"{PREFIX}-start", style={"padding": "0.75rem 1rem", "marginBottom": "1rem"}),
                    html.Div(id=f"{PREFIX}-body"),
                ],
                style={"maxWidth": "1100px", "margin": "0 auto", "padding": "1.5rem"},
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        Output(f"{PREFIX}-state", "data"),
        Output(f"{PREFIX}-body", "children"),
        Input(f"{PREFIX}-start", "n_clicks"),
        Input(f"{PREFIX}-submit", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-next", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-restart", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-drag-state", "data", allow_optional=True),
        State(f"{PREFIX}-state", "data"),
        State({"type": f"{PREFIX}-word", "index": ALL, "word": ALL}, "children"),
    )
    def update_game(_start_clicks, _submit_clicks, _next_clicks, _restart_clicks, drag_state, state, _word_children):
        trigger = ctx.triggered_id

        if not state or not state.get("initialized"):
            state = _new_game_state()

        if trigger in (None, f"{PREFIX}-start", f"{PREFIX}-restart"):
            if trigger in (f"{PREFIX}-start", f"{PREFIX}-restart"):
                state = _new_game_state()
        elif trigger == f"{PREFIX}-drag-state":
            placements = drag_state or {}
            state["placements"] = placements
            verse = VERSES[state["index"]]
            state["answers"] = [placements.get(str(i), "") for i in range(len(verse["blanks"]))]
        elif trigger == f"{PREFIX}-submit":
            verse = VERSES[state["index"]]
            state["answers"] = [state.get("placements", {}).get(str(i), "") for i in range(len(verse["blanks"]))]
            state["submitted"] = True
            correct_count = sum(
                1
                for value, expected in zip(state["answers"], verse["blanks"])
                if (value or "").strip().lower() == expected.lower()
            )
            state["score"] += correct_count
            state["results"].append(
                {
                    "reference": verse["reference"],
                    "correct_count": correct_count,
                    "total": len(verse["blanks"]),
                }
            )
        elif trigger == f"{PREFIX}-next":
            if state.get("submitted"):
                state["index"] += 1
                state["submitted"] = False
                state["answers"] = []
                state["placements"] = {}

        return state, _render_game(state)
