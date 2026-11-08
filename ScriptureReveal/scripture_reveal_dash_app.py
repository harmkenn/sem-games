"""Dash page for the Scripture Reveal team game."""

import random
import re
import time
from math import ceil

from dash import Input, Output, State, ctx, dcc, html

from scripture_data import ALL_REFERENCES, VERSES


PREFIX = "sr"
ROUND_SECONDS = 60


def _tokenize(text):
    return re.findall(r"\s+|[\w]+(?:['’][\w]+)*|[^\w\s]", text)


def _word_count(text):
    return sum(bool(re.search(r"\w", token)) for token in _tokenize(text))


def _new_round(state):
    verse = VERSES[state["verse_order"][state["round_index"]]]
    state["reveal_order"] = list(range(_word_count(verse["text"])))
    random.shuffle(state["reveal_order"])
    state["bank_order"] = list(range(_word_count(verse["text"])))
    random.shuffle(state["bank_order"])
    if len(state["bank_order"]) > 1 and state["bank_order"] == list(range(len(state["bank_order"]))):
        state["bank_order"][0], state["bank_order"][1] = state["bank_order"][1], state["bank_order"][0]
    state["elapsed"] = 0.0
    state["started_at"] = None
    state["status"] = "ready"
    state["guessed_teams"] = []
    state["claimed_team"] = None
    state["result"] = None
    state["placements"] = {}


def _new_game():
    verse_order = list(range(len(VERSES)))
    random.shuffle(verse_order)
    state = {
        "initialized": True,
        "verse_order": verse_order,
        "round_index": 0,
        "scores": [0, 0],
        "status": "ready",
        "elapsed": 0.0,
        "started_at": None,
        "guessed_teams": [],
        "claimed_team": None,
        "result": None,
    }
    _new_round(state)
    return state


def _elapsed(state, now=None):
    elapsed = float(state.get("elapsed", 0))
    if state.get("status") == "running" and state.get("started_at") is not None:
        elapsed += max(0.0, (time.time() if now is None else now) - state["started_at"])
    return min(ROUND_SECONDS, elapsed)


def _remaining(state, now=None):
    return max(0.0, ROUND_SECONDS - _elapsed(state, now))


def _normalized_reference(reference):
    return re.sub(r"[\s–—-]+", "", (reference or "").casefold())


def _visible_word_indexes(state):
    elapsed = _elapsed(state)
    word_count = len(state["reveal_order"])
    revealed_count = min(word_count, int(elapsed / ROUND_SECONDS * word_count))
    return set(state["reveal_order"][:revealed_count])


def _active_placements(placements, visible_words, word_count):
    active = {}
    used_words = set()
    for slot, word in (placements or {}).items():
        try:
            slot_index, word_index = int(slot), int(word)
        except (TypeError, ValueError):
            continue
        if (
            slot_index < 0
            or word_index < 0
            or slot_index >= word_count
            or word_index >= word_count
            or slot_index in visible_words
            or word_index in visible_words
            or word_index in used_words
        ):
            continue
        active[str(slot_index)] = word_index
        used_words.add(word_index)
    return active


def _scoreboard(scores):
    colors = ["#2563EB", "#DC2626"]
    return html.Div(
        [
            html.Div(
                f"Team {index + 1}: {score}",
                style={
                    "backgroundColor": colors[index],
                    "color": "white",
                    "fontSize": "1.25rem",
                    "fontWeight": "bold",
                    "padding": "0.8rem 1rem",
                    "borderRadius": "10px",
                    "textAlign": "center",
                },
            )
            for index, score in enumerate(scores)
        ],
        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "0.75rem"},
    )


def _render_verse(verse, state):
    visible_words = _visible_word_indexes(state)
    placements = _active_placements(state.get("placements"), visible_words, len(state["reveal_order"]))
    placed_words = set(placements.values())
    can_edit = state["status"] in ("ready", "running", "paused", "claimed")
    word_tokens = [
        token for token in _tokenize(verse["text"]) if re.search(r"\w", token)
    ]
    word_index = 0
    tokens = []
    word_bank = {}
    for token in _tokenize(verse["text"]):
        if re.search(r"\w", token):
            index = word_index
            word_index += 1
            is_visible = index in visible_words
            placed_word = placements.get(str(index))
            displayed_word = token if is_visible else (
                word_tokens[placed_word] if placed_word is not None else "________"
            )
            tokens.append(
                html.Span(
                    displayed_word,
                    className="sr-slot",
                    draggable="true" if placed_word is not None and can_edit else "false",
                    **{
                        "data-index": str(index),
                        "data-word-index": "" if placed_word is None else str(placed_word),
                    },
                    style={
                        "backgroundColor": "transparent" if is_visible else "#DBEAFE",
                        "borderRadius": "4px",
                        "color": "#0F172A" if is_visible or placed_word is not None else "#64748B",
                        "fontWeight": "bold" if is_visible or placed_word is not None else "normal",
                        "borderBottom": "2px solid #94A3B8" if not is_visible else "none",
                        "cursor": "grab" if placed_word is not None and can_edit else "default",
                    },
                )
            )
            if index not in visible_words and index not in placed_words:
                word_bank[index] = html.Span(
                    token,
                    className="sr-word",
                    draggable="true" if can_edit else "false",
                    **{"data-word-index": str(index)},
                    style={
                        "display": "inline-block",
                        "padding": "0.45rem 0.65rem",
                        "backgroundColor": "#E0E7FF",
                        "border": "1px solid #A5B4FC",
                        "borderRadius": "8px",
                        "color": "#1E1B4B",
                        "fontWeight": "bold",
                        "cursor": "grab" if can_edit else "default",
                        "userSelect": "none",
                    },
                )
        else:
            tokens.append(token)

    bank_order = state.get("bank_order", list(range(len(state["reveal_order"]))))
    word_bank = [word_bank[index] for index in bank_order if index in word_bank]

    return html.Div(
        [
            html.Div(
                tokens,
                style={
                    "fontSize": "1.5rem",
                    "lineHeight": 2,
                    "padding": "1.5rem",
                    "backgroundColor": "#F8FAFC",
                    "border": "2px solid #CBD5E1",
                    "borderRadius": "12px",
                    "whiteSpace": "pre-wrap",
                    "overflowWrap": "anywhere",
                    "flex": "2 1 32rem",
                    "minWidth": 0,
                },
            ),
            html.Div(
                [
                    html.H4(f"Remaining words ({len(word_bank)})", style={"marginTop": 0}),
                    html.Div(
                        word_bank,
                        id=f"{PREFIX}-word-bank",
                        style={
                            "display": "flex",
                            "alignContent": "flex-start",
                            "gap": "0.5rem",
                            "flexWrap": "wrap",
                            "maxHeight": "28rem",
                            "overflowY": "auto",
                            "padding": "0.75rem",
                            "backgroundColor": "#EEF2FF",
                            "border": "1px solid #C7D2FE",
                            "borderRadius": "10px",
                            "minHeight": "5rem",
                        },
                    ),
                    html.P("Drag words into the blanks.", style={"fontSize": "0.9rem"}),
                ],
                style={"flex": "1 1 15rem", "minWidth": "14rem"},
            ),
        ],
        id=f"{PREFIX}-board",
        **{"data-can-edit": str(can_edit).lower()},
        style={
            "display": "flex",
            "alignItems": "flex-start",
            "gap": "1rem",
            "flexWrap": "wrap",
        },
    )


def _render(state):
    if state["status"] == "complete":
        if state["round_index"] + 1 >= len(state["verse_order"]):
            high_score = max(state["scores"])
            winners = [i + 1 for i, score in enumerate(state["scores"]) if score == high_score]
            winner = (
                f"Team {winners[0]} wins!"
                if len(winners) == 1
                else f"Teams {', '.join(map(str, winners))} tie!"
            )
            return html.Div(
                [
                    html.H2("Game complete"),
                    html.H3(winner),
                    _scoreboard(state["scores"]),
                    html.Button("Play again", id=f"{PREFIX}-restart"),
                ]
            )

    if state["status"] == "expired" and state["round_index"] + 1 >= len(state["verse_order"]):
        return html.Div(
            [
                html.H2("Game complete"),
                html.H3("Time ran out on the final scripture."),
                _scoreboard(state["scores"]),
                html.Button("Play again", id=f"{PREFIX}-restart"),
            ]
        )

    verse = VERSES[state["verse_order"][state["round_index"]]]
    remaining = _remaining(state)
    timer = ceil(remaining)
    timer_color = "#DC2626" if timer <= 5 else "#0F172A"
    timer_control = None
    if state["status"] == "ready":
        timer_control = html.Button("Start", id=f"{PREFIX}-start")
    elif state["status"] == "running":
        timer_control = html.Button("Pause", id=f"{PREFIX}-pause")
    elif state["status"] == "paused":
        timer_control = html.Button("Resume", id=f"{PREFIX}-start")

    content = [
        html.H3(f"Scripture {state['round_index'] + 1} of {len(state['verse_order'])}"),
        _scoreboard(state["scores"]),
        html.Div(
            [
                html.Div(
                    f"{timer // 60:02d}:{timer % 60:02d}",
                    style={
                        "fontSize": "3.5rem",
                        "fontWeight": "bold",
                        "color": timer_color,
                        "fontVariantNumeric": "tabular-nums",
                    },
                ),
                timer_control,
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "gap": "1rem",
                "margin": "1rem 0",
            },
        ),
        _render_verse(verse, state),
    ]

    if state["status"] == "ready":
        content.append(html.P("All words are hidden. Start the 60-second clock when both teams are ready."))
    elif state["status"] == "running":
        content.append(html.P("Call STOP when your team can recite the whole scripture."))
        content.append(
            html.Div(
                [
                    html.Button(
                        f"Team {team} calls STOP",
                        id=f"{PREFIX}-claim-{team}",
                        disabled=team - 1 in state["guessed_teams"],
                        style={"padding": "0.75rem 1rem"},
                    )
                    for team in (1, 2)
                ],
                style={"display": "flex", "gap": "0.75rem", "flexWrap": "wrap"},
            )
        )
    elif state["status"] == "paused":
        content.append(html.P("Clock paused."))
    elif state["status"] == "claimed":
        team = state["claimed_team"] + 1
        content.extend(
            [
                html.H3(f"Team {team} called STOP"),
                html.P("Have them recite the whole scripture, then enter the reference they named."),
                dcc.Dropdown(
                    id=f"{PREFIX}-reference",
                    options=[{"label": reference, "value": reference} for reference in ALL_REFERENCES],
                    placeholder="Select scripture reference",
                    clearable=True,
                    searchable=True,
                    style={"maxWidth": "24rem"},
                ),
                html.Div(
                    [
                        html.Button("Correct reading", id=f"{PREFIX}-correct"),
                        html.Button("Incorrect reading", id=f"{PREFIX}-incorrect"),
                    ],
                    style={"display": "flex", "gap": "0.75rem", "marginTop": "0.75rem"},
                ),
            ]
        )
    elif state["status"] == "complete":
        result = state["result"]
        content.extend(
            [
                html.H3(
                    f"Team {result['team'] + 1} earned {result['total']} points "
                    f"({result['time_points']} for time, {result['reference_points']} for reference)."
                ),
                html.P(f"Answer: {verse['reference']}"),
                html.Button("Next scripture", id=f"{PREFIX}-next"),
            ]
        )
    elif state["status"] == "expired":
        content.extend(
            [
                html.H3("Time is up!"),
                html.P(f"Answer: {verse['reference']}"),
                html.Button("Next scripture", id=f"{PREFIX}-next"),
            ]
        )
    return html.Div(content, style={"display": "grid", "gap": "1rem"})


def layout():
    state = _new_game()
    return html.Div(
        [
            dcc.Store(id=f"{PREFIX}-state", storage_type="session", data=state),
            dcc.Store(id=f"{PREFIX}-drag-action", storage_type="memory", data=None),
            dcc.Interval(id=f"{PREFIX}-timer", interval=1000, disabled=True),
            html.Div(
                [
                    html.H2("Scripture Reveal"),
                    html.P(
                        "Two teams race to recite each scripture as its hidden words appear at random. "
                        "A correct recitation earns the seconds remaining; naming the right reference adds 5 points."
                    ),
                    html.Div(id=f"{PREFIX}-body", children=_render(state)),
                ],
                style={"maxWidth": "1000px", "margin": "0 auto", "padding": "1.5rem"},
            ),
        ]
    )


def register_callbacks(app):
    app.clientside_callback(
        """
        function(children) {
            setTimeout(function() {
                var board = document.getElementById('sr-body');
                if (!board || board.dataset.dragBound) return;
                board.dataset.dragBound = 'true';
                var canEdit = function() {
                    var gameBoard = document.getElementById('sr-board');
                    return gameBoard && gameBoard.getAttribute('data-can-edit') === 'true';
                };

                board.addEventListener('dragstart', function(e) {
                    if (!canEdit()) return;
                    var item = e.target.closest('.sr-word, .sr-slot[draggable="true"]');
                    if (!item || !item.hasAttribute('data-word-index')) return;
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('application/json', JSON.stringify({
                        wordIndex: item.getAttribute('data-word-index'),
                        sourceSlot: item.classList.contains('sr-slot')
                            ? item.getAttribute('data-index')
                            : null
                    }));
                });

                board.addEventListener('dragover', function(e) {
                    if (!canEdit()) return;
                    if (e.target.closest('.sr-slot, #sr-word-bank')) e.preventDefault();
                });

                board.addEventListener('drop', function(e) {
                    if (!canEdit()) return;
                    var slot = e.target.closest('.sr-slot');
                    var bank = e.target.closest('#sr-word-bank');
                    if (!slot && !bank) return;
                    e.preventDefault();

                    var dragged;
                    try {
                        dragged = JSON.parse(e.dataTransfer.getData('application/json'));
                    } catch (_) {
                        return;
                    }
                    var wordIndex = Number(dragged.wordIndex);
                    if (!Number.isInteger(wordIndex)) return;
                    dash_clientside.set_props('sr-drag-action', {
                        data: {
                            word_index: wordIndex,
                            source_slot: dragged.sourceSlot === null
                                ? null
                                : Number(dragged.sourceSlot),
                            target_slot: slot ? Number(slot.getAttribute('data-index')) : null,
                            nonce: Date.now()
                        }
                    });
                });
            }, 100);
            return window.dash_clientside.no_update;
        }
        """,
        Output(f"{PREFIX}-drag-action", "id"),
        Input(f"{PREFIX}-body", "children"),
    )

    @app.callback(
        Output(f"{PREFIX}-state", "data"),
        Output(f"{PREFIX}-body", "children"),
        Output(f"{PREFIX}-timer", "disabled"),
        Input(f"{PREFIX}-start", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-pause", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-claim-1", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-claim-2", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-correct", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-incorrect", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-next", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-restart", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-timer", "n_intervals"),
        Input(f"{PREFIX}-drag-action", "data"),
        State(f"{PREFIX}-reference", "value", allow_optional=True),
        State(f"{PREFIX}-state", "data"),
        prevent_initial_call=True,
    )
    def update_game(
        _start, _pause, _claim_1, _claim_2, _correct, _incorrect,
        _next, _restart, _ticks, drag_action, reference, state,
    ):
        state = state or _new_game()
        trigger = ctx.triggered_id
        now = time.time()

        if trigger == f"{PREFIX}-start" and state["status"] in ("ready", "paused"):
            state["started_at"] = now
            state["status"] = "running"
        elif trigger == f"{PREFIX}-pause" and state["status"] == "running":
            state["elapsed"] = _elapsed(state, now)
            state["started_at"] = None
            state["status"] = "paused"
        elif trigger in (f"{PREFIX}-claim-1", f"{PREFIX}-claim-2") and state["status"] == "running":
            team = int(trigger.rsplit("-", 1)[1]) - 1
            if team not in state["guessed_teams"]:
                state["elapsed"] = _elapsed(state, now)
                state["started_at"] = None
                state["claimed_team"] = team
                state["status"] = "claimed"
        elif trigger == f"{PREFIX}-correct" and state["status"] == "claimed":
            verse = VERSES[state["verse_order"][state["round_index"]]]
            time_points = ceil(_remaining(state, now))
            reference_points = (
                5 if _normalized_reference(reference) == _normalized_reference(verse["reference"]) else 0
            )
            total = time_points + reference_points
            team = state["claimed_team"]
            state["scores"][team] += total
            state["result"] = {
                "team": team,
                "time_points": time_points,
                "reference_points": reference_points,
                "total": total,
            }
            state["status"] = "complete"
        elif trigger == f"{PREFIX}-incorrect" and state["status"] == "claimed":
            team = state["claimed_team"]
            state["guessed_teams"].append(team)
            state["status"] = (
                "expired"
                if _remaining(state, now) <= 0 or len(state["guessed_teams"]) == 2
                else "running"
            )
            state["started_at"] = now if state["status"] == "running" else None
        elif trigger == f"{PREFIX}-timer" and state["status"] == "running":
            if _elapsed(state, now) >= ROUND_SECONDS:
                state["elapsed"] = ROUND_SECONDS
                state["status"] = "expired"
                state["started_at"] = None
        elif trigger == f"{PREFIX}-drag-action" and state["status"] in (
            "ready",
            "running",
            "paused",
            "claimed",
        ):
            action = drag_action or {}
            visible_words = _visible_word_indexes(state)
            placements = _active_placements(
                state.get("placements"),
                visible_words,
                len(state["reveal_order"]),
            )
            try:
                word_index = int(action["word_index"])
                target_slot = action.get("target_slot")
                source_slot = action.get("source_slot")
                target_slot = None if target_slot is None else int(target_slot)
                source_slot = None if source_slot is None else int(source_slot)
            except (KeyError, TypeError, ValueError):
                word_index = -1
                target_slot = None
                source_slot = None

            if source_slot is not None and placements.get(str(source_slot)) == word_index:
                del placements[str(source_slot)]
            if (
                target_slot is not None
                and 0 <= word_index < len(state["reveal_order"])
                and 0 <= target_slot < len(state["reveal_order"])
                and word_index not in visible_words
                and target_slot not in visible_words
                and word_index not in placements.values()
            ):
                placements[str(target_slot)] = word_index
            state["placements"] = placements
        elif trigger == f"{PREFIX}-next" and state["status"] in ("complete", "expired"):
            state["round_index"] += 1
            if state["round_index"] < len(state["verse_order"]):
                _new_round(state)
        elif trigger == f"{PREFIX}-restart":
            state = _new_game()

        return state, _render(state), state["status"] != "running"
