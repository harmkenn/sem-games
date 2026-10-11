"""Dash page for the Guess Who game."""

import random
import re
import time

from dash import ALL, Input, Output, State, ctx, dcc, html

from who_data import character_data


PREFIX = "gw"
TEAM_COLORS = ["#FF4B4B", "#007BFF", "#2ECC71", "#F4B400"]
HINT_REVEAL_INTERVAL = 15
GUESS_TIME_LIMIT = 15
WAITING = "waiting_for_hint_reveal"
BUZZED = "buzzed_in_guess"
REVEALED = "answer_revealed"


def clean_character_name(name):
    return re.sub(r"\(.*\)", "", name).strip()


def build_character_options(correct_character, all_characters, num_options=10):
    cleaned_correct = clean_character_name(correct_character)
    available = [
        name for name in all_characters
        if clean_character_name(name) != cleaned_correct
    ]
    distractor_count = min(num_options - 1, len(available))
    options = random.sample(available, distractor_count) if distractor_count else []
    options.append(correct_character)
    random.shuffle(options)
    return options


def _setup_question(state):
    character = state["questions"][state["question_index"]]
    all_names = [item["character_name"] for item in character_data]
    state["options"] = build_character_options(character["character_name"], all_names)
    hint_indexes = list(range(len(character["hints"])))
    random.shuffle(hint_indexes)
    state["hint_indexes"] = hint_indexes
    state["question_started"] = time.time()
    state["frozen_elapsed"] = 0
    state["timer_stopped"] = False
    state["selected_option"] = None
    state["question_answered"] = False
    state["buzzed_team"] = None
    state["guess_started"] = None
    state["guessed_this_round"] = [False] * len(state["scores"])
    state["phase"] = WAITING


def _new_game(team_count):
    state = {
        "initialized": True,
        "questions": random.sample(character_data, len(character_data)),
        "question_index": 0,
        "scores": [0] * team_count,
        "history": [],
        "phase": WAITING,
        "timer_stopped": False,
        "question_answered": False,
    }
    _setup_question(state)
    return state


def _elapsed(state, now):
    if state["phase"] != WAITING or state["timer_stopped"]:
        return float(state.get("frozen_elapsed", 0))
    return max(0, now - state["question_started"])


def _hints_to_show(character, elapsed):
    return min(
        len(character["hints"]),
        max(1, int(elapsed // HINT_REVEAL_INTERVAL) + 1),
    )


def _hint_components(character, state, hint_count):
    indexes = state["hint_indexes"][:hint_count]
    return html.Div(
        [
            html.Div(
                [html.Strong(f"Hint {i + 1}: "), character["hints"][hint_index]],
                style={"marginBottom": "0.8rem", "color": "#111"},
            )
            for i, hint_index in enumerate(indexes)
        ],
        style={
            "fontSize": "1.5rem",
            "lineHeight": 1.6,
            "padding": "1rem",
            "backgroundColor": "#f0f2f6",
            "borderRadius": "12px",
            "marginBottom": "1rem",
        },
    )


def _scoreboard(scores, final=False):
    return html.Div(
        [
            html.Div(
                f"Team {i + 1}: {score}{' points' if final else ''}",
                style={
                    "backgroundColor": TEAM_COLORS[i],
                    "color": "white",
                    "fontSize": "1.4rem",
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "padding": "0.8rem",
                    "borderRadius": "12px",
                    "margin": "0.3rem",
                },
            )
            for i, score in enumerate(scores)
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": f"repeat({len(scores)}, minmax(0, 1fr))",
            "gap": "0.4rem",
        },
    )


def _render(state):
    if not state or not state.get("initialized"):
        return html.Div("Starting Guess Who…")
    scores = state["scores"]
    if state["question_index"] >= len(state["questions"]):
        return html.Div(
            [
                html.H2("🎉 Game Complete!"),
                html.H3("📊 Final Scores"),
                _scoreboard(scores, final=True),
                html.Button("🔁 Play Again", id=f"{PREFIX}-play-again"),
            ]
        )

    question_number = state["question_index"] + 1
    character = state["questions"][state["question_index"]]
    now = time.time()
    elapsed = _elapsed(state, now)
    hint_count = _hints_to_show(character, elapsed)
    points = max(100, 500 - hint_count * 100)
    phase = state["phase"]

    content = [
        html.H2(f"Question {question_number} of {len(state['questions'])}"),
        html.H3("📋 Character Choice Board", style={"textAlign": "center"}),
        html.Div(
            [
                html.Button(
                    f"⭐ {option}" if option == state.get("selected_option") else option,
                    id={"type": f"{PREFIX}-option", "index": index},
                    n_clicks=0,
                    style={
                        "fontSize": "1.1rem",
                        "padding": "0.8rem",
                        "width": "100%",
                        "minHeight": "4rem",
                        "whiteSpace": "normal",
                    },
                )
                for index, option in enumerate(state["options"])
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(5, minmax(0, 1fr))",
                "gap": "0.5rem",
            },
        ),
        html.Hr(),
        html.Div(
            f"⏱️ Time: {int(elapsed)}s | Value: {points} pts",
            style={"fontSize": "1.5rem", "fontWeight": "bold", "color": "#D97706"},
        ),
    ]
    if phase == WAITING:
        content.append(
            html.Button(
                "▶ RESUME CLOCK" if state["timer_stopped"] else "🛑 STOP CLOCK",
                id=f"{PREFIX}-clock",
            )
        )
        if state.get("history"):
            previous = state["history"][-1]
            if previous["question_num"] == question_number and not previous["is_correct"]:
                content.append(
                    html.Div(
                        f"Team {previous['team']} guessed “{previous['guess']}” "
                        f"and lost {abs(previous['points'])} points.",
                        style={"color": "#9A3412"},
                    )
                )
        content.append(_hint_components(character, state, hint_count))
        if hint_count == len(character["hints"]):
            content.extend(
                [
                    html.Div("All hints revealed!"),
                    html.Button("Show Answer", id=f"{PREFIX}-show-answer"),
                ]
            )
        content.append(html.H4("Who's buzzing in?"))
        content.append(
            html.Div(
                [
                    html.Button(
                        f"Team {team + 1} Buzz!",
                        id={"type": f"{PREFIX}-buzz", "index": team},
                        n_clicks=0,
                        disabled=state["guessed_this_round"][team],
                    )
                    for team in range(len(scores))
                ],
                style={"display": "flex", "gap": "0.7rem"},
            )
        )
    elif phase == BUZZED:
        team = state["buzzed_team"]
        remaining = max(0, GUESS_TIME_LIMIT - (now - state["guess_started"]))
        content.extend(
            [
                html.H4(f"🔔 Team {team + 1} Buzzed In! You have {GUESS_TIME_LIMIT} seconds."),
                html.Div(f"Time remaining: {int(remaining)} seconds"),
                _hint_components(character, state, hint_count),
                html.Div(
                    f"Selected guess: {state.get('selected_option') or 'No one selected yet'}",
                    style={
                        "fontSize": "1.2rem",
                        "fontWeight": "bold",
                        "margin": "0.8rem 0",
                        "color": "#111827",
                    },
                ),
                html.Button(
                    "Submit Guess",
                    id={"type": f"{PREFIX}-submit", "index": question_number},
                ),
            ]
        )
    if state.get("question_answered") or phase == REVEALED:
        if state["history"] and state["history"][-1]["question_num"] == question_number:
            result = state["history"][-1]
            if result["is_correct"]:
                message = f"✅ Correct! Team {result['team']} earned {result['points']} points!"
                color = "#10B981"
            else:
                message = f"❌ Incorrect guess! Team {result['team']} guessed “{result['guess']}”. -100 points."
                color = "#EF4444"
            content.append(
                html.Div(
                    message,
                    style={"backgroundColor": color, "color": "white", "padding": "1rem", "fontWeight": "bold"},
                )
            )
        else:
            content.append(html.Div("ℹ️ Answer revealed without a correct guess."))
        content.extend(
            [
                html.H3(
                    f"The character was: {character['character_name']}",
                    style={"textAlign": "center"},
                ),
                html.Button(
                    "➡️ Next Character",
                    id={"type": f"{PREFIX}-next", "index": question_number},
                ),
            ]
        )
    content.extend([html.Hr(), html.H3("📊 Current Scores"), _scoreboard(scores)])
    return html.Div(content)


def layout():
    return html.Div(
        [
            dcc.Store(id=f"{PREFIX}-state", storage_type="session", data={}),
            dcc.Interval(id=f"{PREFIX}-timer", interval=1000, n_intervals=0),
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
        Input(f"{PREFIX}-new-game", "n_clicks"),
        Input(f"{PREFIX}-timer", "n_intervals"),
        Input(f"{PREFIX}-play-again", "n_clicks", allow_optional=True),
        Input({"type": f"{PREFIX}-option", "index": ALL}, "n_clicks"),
        Input({"type": f"{PREFIX}-buzz", "index": ALL}, "n_clicks"),
        Input(f"{PREFIX}-clock", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-show-answer", "n_clicks", allow_optional=True),
        Input({"type": f"{PREFIX}-guess", "index": ALL}, "value"),
        Input({"type": f"{PREFIX}-submit", "index": ALL}, "n_clicks"),
        Input({"type": f"{PREFIX}-next", "index": ALL}, "n_clicks"),
        State(f"{PREFIX}-state", "data"),
        State({"type": f"{PREFIX}-guess", "index": ALL}, "value"),
    )
    def update_game(team_count, _new_clicks, _ticks, _play_clicks, _option_clicks,
                    _buzz_clicks, _clock_clicks, _show_clicks, guess_values,
                    _submit_clicks, _next_clicks, state, selected_guesses):
        trigger = ctx.triggered_id
        if not state or not state.get("initialized"):
            state = _new_game(team_count or 2)
        elif trigger in (f"{PREFIX}-new-game", f"{PREFIX}-play-again"):
            state = _new_game(team_count or len(state["scores"]))
        elif trigger == f"{PREFIX}-team-count" and len(state["scores"]) != team_count:
            state = _new_game(team_count or 2)
        elif isinstance(trigger, dict):
            action = trigger.get("type")
            index = trigger.get("index")
            if action == f"{PREFIX}-option":
                if 0 <= index < len(state["options"]):
                    state["selected_option"] = state["options"][index]
            elif action == f"{PREFIX}-guess":
                if guess_values and guess_values[0]:
                    state["selected_option"] = guess_values[0]
            elif action == f"{PREFIX}-buzz" and state["phase"] == WAITING:
                if not state["guessed_this_round"][index]:
                    now = time.time()
                    state["frozen_elapsed"] = _elapsed(state, now)
                    state["buzzed_team"] = index
                    state["guess_started"] = now
                    state["phase"] = BUZZED
            elif action == f"{PREFIX}-submit" and state["phase"] == BUZZED:
                team = state["buzzed_team"]
                character = state["questions"][state["question_index"]]
                guess = (
                    selected_guesses[0]
                    if selected_guesses and selected_guesses[0]
                    else state.get("selected_option")
                )
                if guess:
                    elapsed = state["frozen_elapsed"]
                    hint_count = _hints_to_show(character, elapsed)
                    correct = clean_character_name(guess) == clean_character_name(character["character_name"])
                    earned = max(100, 500 - hint_count * 100) if correct else -100
                    state["scores"][team] += earned
                    result = {
                        "question_num": state["question_index"] + 1,
                        "character_name": character["character_name"],
                        "guess": guess,
                        "is_correct": correct,
                        "points": earned,
                        "team": team + 1,
                    }
                    state["history"].append(result)
                    if correct:
                        state["phase"] = REVEALED
                        state["question_answered"] = True
                    else:
                        state["guessed_this_round"][team] = True
                        if all(state["guessed_this_round"]):
                            state["phase"] = REVEALED
                            state["question_answered"] = True
                        else:
                            state["phase"] = WAITING
                            state["question_started"] = time.time() - elapsed
                        state["buzzed_team"] = None
            elif action == f"{PREFIX}-next" and state["phase"] == REVEALED:
                state["question_index"] += 1
                if state["question_index"] < len(state["questions"]):
                    _setup_question(state)
        elif trigger == f"{PREFIX}-clock" and state["phase"] == WAITING:
            now = time.time()
            if state["timer_stopped"]:
                state["question_started"] = now - state["frozen_elapsed"]
                state["timer_stopped"] = False
            else:
                state["frozen_elapsed"] = _elapsed(state, now)
                state["timer_stopped"] = True
        elif trigger == f"{PREFIX}-show-answer" and state["phase"] == WAITING:
            character = state["questions"][state["question_index"]]
            if _hints_to_show(character, _elapsed(state, time.time())) == len(character["hints"]):
                state["phase"] = REVEALED
                state["question_answered"] = True

        if state["phase"] == BUZZED and time.time() - state["guess_started"] >= GUESS_TIME_LIMIT:
            team = state["buzzed_team"]
            elapsed = state["frozen_elapsed"]
            state["scores"][team] -= 100
            state["guessed_this_round"][team] = True
            state["buzzed_team"] = None
            if all(state["guessed_this_round"]):
                state["phase"] = REVEALED
                state["question_answered"] = True
            else:
                state["phase"] = WAITING
                state["question_started"] = time.time() - elapsed
        return state, _render(state)
