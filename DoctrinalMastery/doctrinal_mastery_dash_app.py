"""Dash page for the 2-Team Doctrinal Mastery scripture & reference match game."""

import json
import random
import re

from dash import ALL, Input, Output, State, ctx, dcc, html

from scripture_data import ALL_REFERENCES, VERSES

PREFIX = "dm"


def _new_game_state():
    verse_indices = list(range(len(VERSES)))
    random.shuffle(verse_indices)  # Randomize scripture sequence for this game

    first_verse_index = verse_indices[0]
    initial_shuffled = list(VERSES[first_verse_index]["blanks"])
    random.shuffle(initial_shuffled)

    return {
        "initialized": True,
        "index": 0,
        "verse_order": verse_indices,
        "current_team": 1,
        "scores": {1: 0, 2: 0},
        "submitted": False,
        "answers": [],
        "selected_reference": None,
        "results": [],
        "placements": {},
        "shuffled_bank": initial_shuffled,
    }


def _tokenize(text):
    return re.findall(r"\b[\w']+\b|[^\w\s]", text)


def _render_verse(verse, answer_values=None, submitted=False, shuffled_bank=None, selected_reference=None):
    answer_values = answer_values or [""] * len(verse["blanks"])
    blank_map = {word.lower(): index for index, word in enumerate(verse["blanks"])}
    seen = set()
    tokens = []

    placed_words = set(w for w in answer_values if w)

    for token in _tokenize(verse["text"]):
        token_lower = token.lower()
        if token_lower in blank_map and token_lower not in seen:
            idx = blank_map[token_lower]
            seen.add(token_lower)
            current_word = answer_values[idx] if len(answer_values) > idx else ""
            is_draggable = "true" if (current_word and not submitted) else "false"

            tokens.append(
                html.Div(
                    current_word if current_word else "_____",
                    id={"type": f"{PREFIX}-slot", "index": idx},
                    className="dm-slot",
                    draggable=is_draggable,
                    **{"data-index": str(idx), "data-word": current_word},
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "minWidth": "120px",
                        "padding": "0.35rem 0.7rem",
                        "margin": "0 0.2rem",
                        "borderRadius": "8px",
                        "border": "2px dashed #0F172A" if not current_word else "2px solid #4F46E5",
                        "backgroundColor": "#EEF2FF" if current_word else "#FFFFFF",
                        "color": "#1E1B4B" if current_word else "#94A3B8",
                        "fontWeight": "bold",
                        "minHeight": "42px",
                        "verticalAlign": "middle",
                        "cursor": "grab" if (current_word and not submitted) else "default",
                    },
                )
            )
        else:
            tokens.append(html.Span(token, style={"whiteSpace": "pre-wrap"}))

        if token and token[-1].isalnum():
            tokens.append(html.Span(" ", style={"whiteSpace": "pre-wrap"}))

    if not shuffled_bank:
        shuffled_bank = list(verse["blanks"])
        random.shuffle(shuffled_bank)

    word_bank = []
    for idx, word in enumerate(shuffled_bank):
        is_placed = word in placed_words
        word_bank.append(
            html.Div(
                word,
                key=f"bank-{idx}",
                id={"type": f"{PREFIX}-word", "index": idx, "word": word},
                className="dm-word",
                draggable="false" if (is_placed or submitted) else "true",
                **{"data-index": str(idx), "data-word": word},
                style={
                    "padding": "0.6rem 0.9rem",
                    "borderRadius": "8px",
                    "backgroundColor": "#F1F5F9" if is_placed else "#E0E7FF",
                    "border": "1px solid #CBD5E1" if is_placed else "1px solid #818CF8",
                    "color": "#94A3B8" if is_placed else "#1E1B4B",
                    "fontWeight": "bold",
                    "cursor": "not-allowed" if (is_placed or submitted) else "grab",
                    "userSelect": "none",
                    "textAlign": "center",
                    "boxShadow": "none" if is_placed else "0 2px 8px rgba(79,70,229,0.15)",
                    "visibility": "hidden" if is_placed else "visible",
                },
            )
        )

    return html.Div(
        [
            # Scripture Reference Dropdown
            html.Div(
                [
                    html.Label(
                        "📌 Identify the Scripture Reference:",
                        style={"fontWeight": "bold", "fontSize": "1.1rem", "marginBottom": "0.5rem", "display": "block"},
                    ),
                    dcc.Dropdown(
                        id=f"{PREFIX}-ref-dropdown",
                        options=[{"label": ref, "value": ref} for ref in ALL_REFERENCES],
                        value=selected_reference,
                        placeholder="-- Select Scripture Reference --",
                        disabled=submitted,
                        style={"maxWidth": "400px", "marginBottom": "1rem"},
                    ),
                ],
                style={"backgroundColor": "#F1F5F9", "padding": "1rem", "borderRadius": "10px", "marginBottom": "1.2rem"},
            ),
            # Verse & Word Bank Section
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
                            html.Div("Word bank (10 words)", style={"fontWeight": "bold", "marginBottom": "0.7rem"}),
                            html.Div(
                                word_bank,
                                id=f"{PREFIX}-word-bank",
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(120px, 1fr))",
                                    "gap": "0.6rem",
                                    "padding": "0.75rem",
                                    "backgroundColor": "#EEF2FF",
                                    "borderRadius": "10px",
                                    "border": "1px solid #C7D2FE",
                                    "minHeight": "100px",
                                },
                            ),
                        ],
                        style={"minWidth": "220px", "maxWidth": "260px", "marginLeft": "1rem"},
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
        t1_score = state["scores"].get("1", state["scores"].get(1, 0))
        t2_score = state["scores"].get("2", state["scores"].get(2, 0))

        if t1_score > t2_score:
            winner = "🏆 Team 1 Wins!"
        elif t2_score > t1_score:
            winner = "🏆 Team 2 Wins!"
        else:
            winner = "🤝 It's a Tie!"

        return html.Div(
            [
                html.H2("🎉 Practice Complete!"),
                html.H3(winner, style={"color": "#2563EB", "margin": "1rem 0"}),
                html.Div(
                    [
                        html.Div(f"🔵 Team 1 Final Score: {t1_score}", style={"fontSize": "1.2rem"}),
                        html.Div(f"🔴 Team 2 Final Score: {t2_score}", style={"fontSize": "1.2rem"}),
                    ],
                    style={"marginBottom": "1.5rem", "display": "flex", "gap": "2rem"},
                ),
                html.Button("🔁 Start Again", id=f"{PREFIX}-restart", style={"padding": "0.75rem 1rem"}),
            ],
            style={"padding": "1rem", "maxWidth": "900px"},
        )

    current_verse_idx = state["verse_order"][state["index"]]
    verse = VERSES[current_verse_idx]

    answer_values = state.get("answers", [""] * len(verse["blanks"]))
    correct_answers = [word for word in verse["blanks"]]
    current_team = state.get("current_team", 1)

    t1_score = state["scores"].get("1", state["scores"].get(1, 0))
    t2_score = state["scores"].get("2", state["scores"].get(2, 0))

    team_color = "#2563EB" if current_team == 1 else "#DC2626"

    content = [
        html.Div(
            [
                html.H3("Doctrinal Mastery Match & Fill-In", style={"margin": "0"}),
                html.Div(
                    [
                        html.Span(
                            f"🔵 Team 1: {t1_score}",
                            style={
                                "fontWeight": "bold" if current_team == 1 else "normal",
                                "color": "#2563EB",
                                "padding": "0.4rem 0.8rem",
                                "borderRadius": "6px",
                                "backgroundColor": "#DBEAFE" if current_team == 1 else "transparent",
                            },
                        ),
                        html.Span(
                            f"🔴 Team 2: {t2_score}",
                            style={
                                "fontWeight": "bold" if current_team == 2 else "normal",
                                "color": "#DC2626",
                                "padding": "0.4rem 0.8rem",
                                "borderRadius": "6px",
                                "backgroundColor": "#FEE2E2" if current_team == 2 else "transparent",
                            },
                        ),
                    ],
                    style={"display": "flex", "gap": "1rem", "alignItems": "center"},
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "1rem",
            },
        ),
        html.Div(
            f"Round {state['index'] + 1} of {len(VERSES)} • CURRENT TURN: TEAM {current_team}",
            style={"marginBottom": "1rem", "fontWeight": "bold", "color": team_color, "fontSize": "1.1rem"},
        ),
        _render_verse(verse, answer_values, state.get("submitted", False), state.get("shuffled_bank"), state.get("selected_reference")),
    ]

    if state.get("submitted"):
        correct_words = sum(
            1 for value, expected in zip(answer_values, correct_answers) if value.strip().lower() == expected.lower()
        )
        is_ref_correct = state.get("selected_reference") == verse["reference"]
        ref_points = 5 if is_ref_correct else 0
        total_round_pts = correct_words + ref_points
        next_team = 2 if current_team == 1 else 1

        correct_ref_text = verse["reference"]
        ref_status_msg = "✅ Correct (+5 pts)" if is_ref_correct else f"❌ Incorrect (Correct was: {correct_ref_text})"

        content.extend(
            [
                html.Div(
                    [
                        html.Div(f"Team {current_team} scored {total_round_pts} points this round!"),
                        html.Div(f"• Words: {correct_words}/10 correct ({correct_words} pts)"),
                        html.Div(f"• Reference: {ref_status_msg}"),
                    ],
                    style={
                        "marginTop": "1rem",
                        "padding": "0.8rem 1rem",
                        "backgroundColor": "#DBEAFE" if current_team == 1 else "#FEE2E2",
                        "borderRadius": "8px",
                        "fontWeight": "bold",
                        "color": team_color,
                    },
                ),
                html.Div(
                    [
                        html.Strong("Answer key: "),
                        ", ".join(correct_answers),
                    ],
                    style={"marginTop": "0.8rem", "fontSize": "1rem"},
                ),
                html.Button(
                    f"➡️ Next Verse (Pass to Team {next_team})",
                    id=f"{PREFIX}-next",
                    style={"marginTop": "1rem", "padding": "0.75rem 1rem"},
                ),
            ]
        )
    else:
        content.append(
            html.Button(
                f"✅ Submit Answers for Team {current_team}",
                id=f"{PREFIX}-submit",
                style={"marginTop": "1rem", "padding": "0.75rem 1rem"},
            )
        )

    return html.Div(content, style={"maxWidth": "1000px", "padding": "1rem"})


def layout():
    return html.Div(
        [
            dcc.Store(id=f"{PREFIX}-state", storage_type="session", data={}),
            dcc.Store(id=f"{PREFIX}-drag-state", storage_type="memory", data={}),
            html.Div(
                [
                    html.H2("📖 Doctrinal Mastery 2-Team Challenge"),
                    html.P("Identify the scripture reference from the list of 24, then drag the 10 missing words into place!"),
                    html.Button("▶ Start 2-Team Game", id=f"{PREFIX}-start", style={"padding": "0.75rem 1rem", "marginBottom": "1rem"}),
                    html.Div(id=f"{PREFIX}-body"),
                ],
                style={"maxWidth": "1100px", "margin": "0 auto", "padding": "1.5rem"},
            ),
        ]
    )


def register_callbacks(app):
    app.clientside_callback(
        """
        function(children) {
            setTimeout(function() {
                var words = document.querySelectorAll('.dm-word[draggable="true"]');
                var slots = document.querySelectorAll('.dm-slot');
                var bank = document.getElementById('dm-word-bank');

                var draggedWord = null;
                var sourceSlotIndex = null;

                function handleDragStart(e) {
                    draggedWord = e.target.getAttribute('data-word');
                    sourceSlotIndex = e.target.getAttribute('data-index');
                    e.dataTransfer.setData('text/plain', draggedWord);
                    e.target.style.opacity = '0.5';
                }

                function handleDragEnd(e) {
                    e.target.style.opacity = '1.0';
                }

                words.forEach(function(word) {
                    word.removeEventListener('dragstart', handleDragStart);
                    word.removeEventListener('dragend', handleDragEnd);
                    word.addEventListener('dragstart', handleDragStart);
                    word.addEventListener('dragend', handleDragEnd);
                });

                slots.forEach(function(slot) {
                    slot.removeEventListener('dragstart', handleDragStart);
                    slot.removeEventListener('dragend', handleDragEnd);
                    
                    if (slot.getAttribute('draggable') === 'true') {
                        slot.addEventListener('dragstart', handleDragStart);
                        slot.addEventListener('dragend', handleDragEnd);
                    }

                    slot.addEventListener('dragover', function(e) {
                        e.preventDefault();
                        slot.style.border = '2px dashed #4F46E5';
                    });

                    slot.addEventListener('dragleave', function(e) {
                        slot.style.border = slot.getAttribute('data-word') ? '2px solid #4F46E5' : '2px dashed #0F172A';
                    });

                    slot.addEventListener('drop', function(e) {
                        e.preventDefault();
                        var targetIndex = slot.getAttribute('data-index');
                        
                        var dragStore = dash_clientside.set_props ? 
                            JSON.parse(sessionStorage.getItem('dm-drag-state') || '{}') : {};

                        if (sourceSlotIndex !== null && sourceSlotIndex !== undefined) {
                            delete dragStore[sourceSlotIndex];
                        }

                        dragStore[targetIndex] = draggedWord;

                        var storeEl = document.getElementById('dm-drag-state');
                        if (storeEl) {
                            dash_clientside.set_props('dm-drag-state', {data: dragStore});
                        }
                    });
                });

                if (bank) {
                    bank.addEventListener('dragover', function(e) { e.preventDefault(); });
                    bank.addEventListener('drop', function(e) {
                        e.preventDefault();
                        if (sourceSlotIndex !== null && sourceSlotIndex !== undefined) {
                            var dragStore = JSON.parse(sessionStorage.getItem('dm-drag-state') || '{}');
                            delete dragStore[sourceSlotIndex];
                            dash_clientside.set_props('dm-drag-state', {data: dragStore});
                        }
                    });
                }
            }, 100);
            return window.dash_clientside.no_update;
        }
        """,
        Output(f"{PREFIX}-drag-state", "id"),
        Input(f"{PREFIX}-body", "children"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output(f"{PREFIX}-state", "data"),
        Output(f"{PREFIX}-body", "children"),
        Input(f"{PREFIX}-start", "n_clicks"),
        Input(f"{PREFIX}-submit", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-next", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-restart", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-drag-state", "data", allow_optional=True),
        Input(f"{PREFIX}-ref-dropdown", "value", allow_optional=True),
        State(f"{PREFIX}-state", "data"),
        State({"type": f"{PREFIX}-word", "index": ALL, "word": ALL}, "children"),
    )
    def update_game(_start_clicks, _submit_clicks, _next_clicks, _restart_clicks, drag_state, ref_selected, state, _word_children):
        trigger = ctx.triggered_id

        if not state or not state.get("initialized"):
            state = _new_game_state()

        if trigger in (None, f"{PREFIX}-start", f"{PREFIX}-restart"):
            if trigger in (f"{PREFIX}-start", f"{PREFIX}-restart"):
                state = _new_game_state()
        elif trigger == f"{PREFIX}-ref-dropdown":
            state["selected_reference"] = ref_selected
        elif trigger == f"{PREFIX}-drag-state":
            placements = drag_state or {}
            state["placements"] = placements
            current_verse_idx = state["verse_order"][state["index"]]
            verse = VERSES[current_verse_idx]
            state["answers"] = [placements.get(str(i), "") for i in range(len(verse["blanks"]))]
        elif trigger == f"{PREFIX}-submit":
            current_verse_idx = state["verse_order"][state["index"]]
            verse = VERSES[current_verse_idx]

            state["answers"] = [state.get("placements", {}).get(str(i), "") for i in range(len(verse["blanks"]))]
            state["submitted"] = True

            correct_words = sum(
                1
                for value, expected in zip(state["answers"], verse["blanks"])
                if (value or "").strip().lower() == expected.lower()
            )
            is_ref_correct = state.get("selected_reference") == verse["reference"]
            round_score = correct_words + (5 if is_ref_correct else 0)

            current_team = str(state.get("current_team", 1))
            state["scores"][current_team] = state["scores"].get(current_team, 0) + round_score
            state["results"].append(
                {
                    "team": current_team,
                    "reference": verse["reference"],
                    "selected_ref": state.get("selected_reference"),
                    "word_score": correct_words,
                    "ref_score": 5 if is_ref_correct else 0,
                    "total": len(verse["blanks"]) + 5,
                }
            )
        elif trigger == f"{PREFIX}-next":
            if state.get("submitted"):
                state["index"] += 1
                state["current_team"] = 2 if state.get("current_team", 1) == 1 else 1
                state["submitted"] = False
                state["answers"] = []
                state["placements"] = {}
                state["selected_reference"] = None

                if state["index"] < len(VERSES):
                    next_verse_idx = state["verse_order"][state["index"]]
                    next_shuffled = list(VERSES[next_verse_idx]["blanks"])
                    random.shuffle(next_shuffled)
                    state["shuffled_bank"] = next_shuffled

        return state, _render_game(state)
