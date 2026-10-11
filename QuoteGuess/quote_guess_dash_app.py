"""Dash page for the Quote Guess game."""

import random
import re

from dash import ALL, Input, Output, State, ctx, dcc, html

from quotes_data import quotes_data


PREFIX = "qg"
TEAM_COLORS = ["#FF4B4B", "#007BFF", "#2ECC71", "#F4B400"]


def clean_speaker_name(speaker):
    return re.sub(r"\(.*\)", "", speaker).strip()


def build_speaker_options(correct_speaker, all_speakers, num_options=10):
    cleaned_names = sorted({clean_speaker_name(name) for name in all_speakers if name})
    correct_cleaned = clean_speaker_name(correct_speaker)
    available = [speaker for speaker in cleaned_names if speaker != correct_cleaned]
    count = min(num_options - 1, len(available))
    options = random.sample(available, count) if count else []
    options.append(correct_speaker)
    random.shuffle(options)
    return options


def _new_game(team_count, question_count):
    selected_quotes = random.sample(quotes_data, min(question_count, len(quotes_data)))
    speakers = sorted({quote["speaker"] for quote in quotes_data if quote.get("speaker")})
    options = {
        str(index): build_speaker_options(quote["speaker"], speakers)
        for index, quote in enumerate(selected_quotes)
    }
    return {
        "initialized": True,
        "questions": selected_quotes,
        "question_index": 0,
        "scores": [0] * team_count,
        "current_team": 0,
        "question_answered": False,
        "hints_shown": [],
        "history": [],
        "speaker_options": options,
        "selected_speaker": options["0"][0] if options["0"] else None,
    }


def _scoreboard(scores, current_team=None, active=True, final=False):
    return html.Div(
        [
            html.Div(
                f"Team {index + 1}: {score}{' points' if final else ''}"
                + (" ⬅️ Current" if active and index == current_team else ""),
                style={
                    "backgroundColor": TEAM_COLORS[index],
                    "color": "white",
                    "fontSize": "1.2rem",
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "padding": "0.8rem",
                    "borderRadius": "10px",
                    "border": "3px solid #000" if active and index == current_team else "none",
                },
            )
            for index, score in enumerate(scores)
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": f"repeat({len(scores)}, minmax(0, 1fr))",
            "gap": "0.6rem",
        },
    )


def _render(state):
    if not state or not state.get("initialized"):
        return html.Div("Starting Quote Guess…")
    scores = state["scores"]
    if state["question_index"] >= len(state["questions"]):
        high_score = max(scores)
        winners = [index + 1 for index, score in enumerate(scores) if score == high_score]
        winner_text = (
            f"🏆 Team {winners[0]} wins with {high_score} points!"
            if len(winners) == 1
            else f"🏆 Teams {', '.join(map(str, winners))} tie with {high_score} points!"
        )
        return html.Div(
            [
                html.H2("🎉 Game Complete!"),
                html.H3("📊 Final Scores"),
                _scoreboard(scores, final=True),
                html.Div(winner_text, style={"margin": "1rem 0"}),
                html.Button("🔁 Play Again", id=f"{PREFIX}-play-again"),
            ]
        )

    index = state["question_index"]
    question_num = index + 1
    quote = state["questions"][index]
    team = state["current_team"]
    hints_shown = state["hints_shown"]
    hints_used = len(hints_shown)
    points = max(300 - hints_used * 100, 0)
    options = state["speaker_options"][str(index)]
    content = [
        html.H2(f"Question {question_num} of {len(state['questions'])}"),
        html.H4(f"🎯 Team {team + 1}'s Turn"),
        html.Div(
            f"“{quote['quote']}”",
            style={
                "fontSize": "1.6rem",
                "fontStyle": "italic",
                "textAlign": "center",
                "color": "#1E3A8A",
                "margin": "1.5rem 0",
                "padding": "1.5rem",
                "backgroundColor": "#DBEAFE",
                "borderRadius": "10px",
                "border": "3px solid #1E3A8A",
                "lineHeight": 1.6,
            },
        ),
        html.H3("Who said this quote?"),
        html.Div(
            [
                html.Button(
                    f"Team {team_index + 1} {'● Active' if team_index == team else ''}".strip(),
                    id={"type": f"{PREFIX}-team", "index": team_index},
                    n_clicks=0,
                    style={"fontWeight": "bold" if team_index == team else "normal"},
                )
                for team_index in range(len(scores))
            ],
            style={"display": "flex", "gap": "0.6rem"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Strong("Available Hints:"),
                        *[
                            html.Div(
                                [
                                    html.Button(
                                        f"💡 Show {hint.split(':', 1)[0]} Hint",
                                        id={"type": f"{PREFIX}-hint", "index": hint_index},
                                        n_clicks=0,
                                    )
                                    if hint_index not in hints_shown
                                    else html.Div(
                                        f"💡 {hint.split(':', 1)[0]}: {hint.split(':', 1)[1].strip()}",
                                        style={
                                            "fontSize": "1.1rem",
                                            "padding": "0.8rem",
                                            "margin": "0.6rem 0",
                                            "backgroundColor": "#FEF3C7",
                                            "borderLeft": "5px solid #F59E0B",
                                            "borderRadius": "5px",
                                            "color": "#78350F",
                                        },
                                    )
                                ],
                                style={"margin": "0.5rem 0"},
                            )
                            for hint_index, hint in enumerate(quote["hints"])
                        ],
                    ],
                    style={"flex": "2"},
                ),
                html.Div(
                    [
                        html.Strong("Points Available:"),
                        html.Div(
                            f"{points} pts",
                            style={
                                "fontSize": "1.5rem",
                                "fontWeight": "bold",
                                "textAlign": "center",
                                "color": "#059669",
                                "backgroundColor": "#D1FAE5",
                                "padding": "1rem",
                                "borderRadius": "8px",
                                "marginTop": "0.5rem",
                            },
                        ),
                    ],
                    style={"flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "1.5rem", "margin": "1rem 0"},
        ),
    ]
    if not state["question_answered"]:
        content.extend(
            [
                html.Hr(),
                dcc.RadioItems(
                    id={"type": f"{PREFIX}-guess", "index": index},
                    options=[{"label": name, "value": name} for name in options],
                    value=state.get("selected_speaker") or (options[0] if options else None),
                    inline=False,
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(5, minmax(0, 1fr))",
                        "gap": "0.75rem",
                        "alignItems": "stretch",
                    },
                    labelStyle={
                        "display": "flex",
                        "alignItems": "center",
                        "padding": "0.7rem 0.8rem",
                        "borderRadius": "8px",
                        "border": "1px solid #D1D5DB",
                        "backgroundColor": "#F8FAFC",
                        "fontSize": "1.05rem",
                        "margin": "0",
                    },
                ),
                html.Button(
                    "✓ Submit Answer",
                    id={"type": f"{PREFIX}-submit", "index": question_num},
                ),
            ]
        )
    else:
        result = state["history"][-1]
        message = (
            f"✓ CORRECT! Team {result['team']} earned {result['points']} points!"
            if result["is_correct"]
            else f"✗ Incorrect! You guessed: {result['guess']}"
        )
        content.extend(
            [
                html.Div(
                    message,
                    style={
                        "fontSize": "1.2rem",
                        "padding": "1rem",
                        "margin": "1rem 0",
                        "backgroundColor": "#10B981" if result["is_correct"] else "#EF4444",
                        "color": "white",
                        "borderRadius": "8px",
                        "textAlign": "center",
                        "fontWeight": "bold",
                    },
                ),
                html.Div(
                    f"The answer was: {result['correct_speaker']}",
                    style={
                        "fontSize": "1.4rem",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "padding": "1rem",
                        "backgroundColor": "#E0E7FF",
                        "border": "2px solid #4F46E5",
                        "borderRadius": "10px",
                        "color": "#1E3A8A",
                    },
                ),
                html.Div(f"Reference: {quote['book']} {quote['chapter']}"),
                html.Button(
                    "➡️ Next Question",
                    id={"type": f"{PREFIX}-next", "index": question_num},
                ),
            ]
        )
    content.extend(
        [
            html.Hr(),
            html.H3("📊 Current Scores"),
            _scoreboard(scores, team, active=not state["question_answered"]),
            html.Button("🔁 Restart Game", id=f"{PREFIX}-restart"),
        ]
    )
    return html.Div(content)


def layout():
    return html.Div(
        [
            dcc.Store(id=f"{PREFIX}-state", storage_type="session", data={}),
            html.Div(
                [
                    html.H3("🎮 Game Setup"),
                    html.Label("Number of teams:"),
                    dcc.Dropdown(
                        id=f"{PREFIX}-team-count",
                        options=[{"label": str(i), "value": i} for i in range(2, 5)],
                        value=2,
                        clearable=False,
                        style={"maxWidth": "12rem"},
                    ),
                    html.Label("Number of questions:"),
                    dcc.Slider(
                        id=f"{PREFIX}-question-count",
                        min=5,
                        max=len(quotes_data),
                        step=1,
                        value=min(10, len(quotes_data)),
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Button("🔁 Start New Game", id=f"{PREFIX}-new-game"),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "1rem", "flexWrap": "wrap"},
            ),
            html.Div(id=f"{PREFIX}-body"),
        ]
    )


def register_callbacks(app):
    @app.callback(
        Output(f"{PREFIX}-state", "data"),
        Output(f"{PREFIX}-body", "children"),
        Input(f"{PREFIX}-team-count", "value"),
        Input(f"{PREFIX}-question-count", "value"),
        Input(f"{PREFIX}-new-game", "n_clicks"),
        Input(f"{PREFIX}-restart", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-play-again", "n_clicks", allow_optional=True),
        Input({"type": f"{PREFIX}-team", "index": ALL}, "n_clicks"),
        Input({"type": f"{PREFIX}-hint", "index": ALL}, "n_clicks"),
        Input({"type": f"{PREFIX}-guess", "index": ALL}, "value"),
        Input({"type": f"{PREFIX}-submit", "index": ALL}, "n_clicks"),
        Input({"type": f"{PREFIX}-next", "index": ALL}, "n_clicks"),
        State(f"{PREFIX}-state", "data"),
        State({"type": f"{PREFIX}-guess", "index": ALL}, "value"),
    )
    def update_game(team_count, question_count, _new_clicks, _restart_clicks,
                    _play_clicks, _team_clicks, _hint_clicks, guess_values,
                    _submit_clicks, _next_clicks, state, selected_guesses):
        trigger = ctx.triggered_id
        if not state or not state.get("initialized"):
            state = _new_game(team_count or 2, question_count or min(10, len(quotes_data)))
        elif trigger in (f"{PREFIX}-new-game", f"{PREFIX}-restart", f"{PREFIX}-play-again"):
            state = _new_game(team_count or len(state["scores"]), question_count or len(state["questions"]))
        elif trigger == f"{PREFIX}-team-count" and len(state["scores"]) != team_count:
            state = _new_game(team_count or 2, question_count or len(state["questions"]))
        elif isinstance(trigger, dict):
            action = trigger.get("type")
            index = trigger.get("index")
            if action == f"{PREFIX}-team" and 0 <= index < len(state["scores"]):
                state["current_team"] = index
            elif action == f"{PREFIX}-hint" and not state["question_answered"]:
                if index not in state["hints_shown"]:
                    state["hints_shown"].append(index)
            elif action == f"{PREFIX}-guess":
                if guess_values and guess_values[0]:
                    state["selected_speaker"] = guess_values[0]
            elif action == f"{PREFIX}-submit" and not state["question_answered"]:
                guess = (
                    selected_guesses[0]
                    if selected_guesses and selected_guesses[0]
                    else state.get("selected_speaker")
                )
                if guess:
                    question = state["questions"][state["question_index"]]
                    correct_speaker = question["speaker"]
                    points = max(300 - len(state["hints_shown"]) * 100, 0)
                    is_correct = guess.lower() == correct_speaker.lower()
                    history = {
                        "question_num": state["question_index"] + 1,
                        "quote": question["quote"],
                        "correct_speaker": correct_speaker,
                        "guess": guess,
                        "is_correct": is_correct,
                        "points": points if is_correct else 0,
                        "team": state["current_team"] + 1,
                        "hints_used": len(state["hints_shown"]),
                    }
                    state["history"].append(history)
                    if is_correct:
                        state["scores"][state["current_team"]] += points
                    state["question_answered"] = True
            elif action == f"{PREFIX}-next" and state["question_answered"]:
                state["question_index"] += 1
                state["question_answered"] = False
                state["hints_shown"] = []
                state["current_team"] = (state["current_team"] + 1) % len(state["scores"])
                if state["question_index"] < len(state["questions"]):
                    options = state["speaker_options"][str(state["question_index"])]
                    state["selected_speaker"] = options[0] if options else None
        return state, _render(state)
