"""
tests.infrastructure.mock_users — 10 Mock Users for RAG Pipeline Test.

Each mock user simulates a complete campaign thread with 4 node outputs
that would be individually embedded.  The content is hand-written to be
semantically distinct across users so vector retrieval can be validated.

Structure per user:
    - thread_id:        Generated at test time (not here)
    - persona_name:     From CONTRACTS.py PERSONA_REGISTRY
    - niche:            Unique business domain
    - node_outputs:     4 dicts with {node_name, text}
    - verifiable_query: Semantic question targeting this user's domain
    - expected_marker:  Phrase that MUST appear in top retrieval results
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockNodeOutput:
    """A single node output to be embedded."""

    node_name: str
    text: str


@dataclass
class MockUser:
    """A simulated campaign user for RAG testing."""

    persona_name: str
    niche: str
    node_outputs: list[MockNodeOutput]
    verifiable_query: str
    expected_marker: str
    thread_id: str = ""  # Assigned at test time


# ---------------------------------------------------------------------------
# The 10 Mock Users
# ---------------------------------------------------------------------------

MOCK_USERS: list[MockUser] = [
    # ── User 1: Silicon Labor × Artisan Coffee ──
    MockUser(
        persona_name="Silicon Labor",
        niche="Artisan coffee roaster",
        verifiable_query="What does the extraction process reveal about craft?",
        expected_marker="single-origin pour-over extraction",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for an artisan coffee roaster that "
                    "treats the craft of single-origin pour-over extraction as a "
                    "meditative practice. The brand believes that the ritual of "
                    "manual brewing is an act of resistance against automated "
                    "consumption."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The water descends through the filter at its own "
                    "pace. The single-origin pour-over extraction is not a method "
                    "— it is a refusal. Each gram measured, each degree calibrated, "
                    "each second observed. The automated drip machine produces "
                    "coffee. The hand produces attention. The object in the cup is "
                    "identical. The labor is not.\n\n"
                    "Image Prompt: Close-up of a glass Chemex carafe, high-contrast "
                    "black and white, 35mm grain, harsh overhead light creating deep "
                    "shadows through the coffee bloom, steam caught in the light "
                    "against a dark void background, 9:16 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.4. The caption successfully embeds "
                    "the single-origin pour-over extraction ritual within a Stoic "
                    "framework of deliberate attention vs. automated consumption. "
                    "The phrase 'the hand produces attention' is a strong "
                    "philosophical anchor. The image prompt correctly specifies "
                    "high-contrast B&W with 35mm grain per persona visual "
                    "constraints. No emoji detected. No prohibited terms."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Campaign for artisan coffee roaster positions the "
                    "pour-over process as philosophical resistance to automated "
                    "consumption. Creative output scored 8.4 on persona alignment "
                    "— strong Stoic register with effective use of the "
                    "observation-vs-production dichotomy. Zero constraint "
                    "violations detected. Recommendation: SHIP. Risk flags: none."
                ),
            ),
        ],
    ),
    # ── User 2: Silicon Labor × Minimalist Architecture ──
    MockUser(
        persona_name="Silicon Labor",
        niche="Minimalist architecture firm",
        verifiable_query="How does empty space define a structure?",
        expected_marker="negative space in brutalist facades",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for a minimalist architecture firm "
                    "that sees negative space in brutalist facades as the true "
                    "material of design. The firm believes that what is removed "
                    "matters more than what remains."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The wall does not speak. The void beside it does. "
                    "Negative space in brutalist facades is not absence — it is "
                    "the deliberate subtraction of noise. Every slab of exposed "
                    "concrete is a decision to leave the surface unfinished, to "
                    "let the structure confess its own weight. The ornament was "
                    "never removed. It was never invited.\n\n"
                    "Image Prompt: Wide shot of a raw concrete facade with deep "
                    "geometric shadow recesses, high-contrast black and white, "
                    "35mm grain, late afternoon directional light carving voids "
                    "into the surface, no humans, 9:16 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.7. The caption demonstrates "
                    "strong command of the Stoic register. The negative space in "
                    "brutalist facades is treated as an active philosophical "
                    "choice rather than decorative absence. The line 'the ornament "
                    "was never invited' is particularly effective. Image prompt "
                    "aligns with high-contrast B&W visual constraints."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Architecture firm campaign leverages the concept of "
                    "negative space as deliberate design philosophy. Vibe score "
                    "8.7 indicates strong persona alignment. The brutalist "
                    "aesthetic maps naturally to the Silicon Labor visual "
                    "language. Recommendation: SHIP. No risk flags."
                ),
            ),
        ],
    ),
    # ── User 3: Silicon Labor × Independent Bookshop ──
    MockUser(
        persona_name="Silicon Labor",
        niche="Independent bookshop",
        verifiable_query="What do old annotations tell us about readers?",
        expected_marker="marginalia in annotated first editions",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for an independent bookshop "
                    "specializing in second-hand volumes. The shop values the "
                    "marginalia in annotated first editions — the pencil marks, "
                    "underlines, and dog-eared pages that reveal a previous "
                    "reader's inner life."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: Someone underlined this sentence in 1973. We do "
                    "not know their name. We know what stopped them. The "
                    "marginalia in annotated first editions is not damage — it "
                    "is correspondence across time. A pencil mark is a letter "
                    "to a stranger who has not yet opened the cover.\n\n"
                    "Image Prompt: Close-up of a yellowed book page with faded "
                    "pencil annotations in the margin, high-contrast black and "
                    "white, 35mm grain, shallow depth of field focusing on a "
                    "single underlined passage, 9:16 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 9.1. Exceptional. The marginalia "
                    "in annotated first editions is transformed into a metaphor "
                    "for temporal communication. The Stoic detachment is "
                    "maintained — the caption observes without sentimentality. "
                    "'A letter to a stranger' is philosophically grounded. "
                    "Image prompt is technically precise."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Bookshop campaign achieves the highest vibe score "
                    "in this batch at 9.1. The concept of marginalia as "
                    "cross-temporal correspondence is original and deeply "
                    "aligned with the Silicon Labor philosophy. "
                    "Recommendation: SHIP. No risk flags."
                ),
            ),
        ],
    ),
    # ── User 4: Silicon Labor × Analog Photography ──
    MockUser(
        persona_name="Silicon Labor",
        niche="Analog photography lab",
        verifiable_query=(
            "What happens in the darkroom that digital cannot replicate?"
        ),
        expected_marker="silver gelatin darkroom processing",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for an analog photography lab "
                    "that still practices silver gelatin darkroom processing. "
                    "The lab believes the chemical process — the uncertainty, "
                    "the waiting, the irreversibility — is what makes a "
                    "photograph real."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The image does not appear instantly. It emerges. "
                    "Silver gelatin darkroom processing is a negotiation between "
                    "chemistry and patience. The developer reveals what the "
                    "shutter captured. The fixer makes the decision permanent. "
                    "There is no undo. There is no filter. There is the grain "
                    "and the grain is the truth.\n\n"
                    "Image Prompt: Darkroom interior, red safelight casting "
                    "deep shadows, a print emerging in a developer tray, "
                    "high-contrast black and white, 35mm grain, close-up of "
                    "gloved hands holding tongs, 9:16 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.6. Silver gelatin darkroom "
                    "processing is framed as an act of irreversible commitment "
                    "— strong Stoic alignment. 'There is no undo' effectively "
                    "contrasts digital impermanence. Image prompt captures "
                    "the darkroom atmosphere within visual constraints."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Photography lab campaign uses the irreversibility "
                    "of silver gelatin processing as its philosophical anchor. "
                    "Vibe score 8.6, solid Stoic voice. The digital-vs-analog "
                    "tension is handled without nostalgia, staying observational. "
                    "Recommendation: SHIP."
                ),
            ),
        ],
    ),
    # ── User 5: Velvet Dispatch × Vintage Watches ──
    MockUser(
        persona_name="Velvet Dispatch",
        niche="Vintage watch restoration",
        verifiable_query="What makes a mechanical movement worth preserving?",
        expected_marker="mechanical calibre heritage movements",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for a vintage watch restoration "
                    "studio that specializes in mechanical calibre heritage "
                    "movements. The studio believes that each movement carries "
                    "the accumulated precision of decades — a machine that "
                    "outlived its maker."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The balance wheel still turns. It has turned since "
                    "1962. The hands that assembled the mechanical calibre "
                    "heritage movements are gone, but the calibre remembers its "
                    "rhythm. We do not repair watches. We continue conversations "
                    "that were started in workshops that no longer exist.\n\n"
                    "Image Prompt: Macro shot of an exposed watch movement with "
                    "patinated brass gears, desaturated teal and amber tones, "
                    "soft grain, golden hour light filtering through a loupe, "
                    "shallow depth of field, 4:5 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.9. The Melancholic register is "
                    "beautifully sustained. Mechanical calibre heritage movements "
                    "are personified without sentimentality — 'the calibre "
                    "remembers its rhythm' is a Benjamin-inflected observation "
                    "on the aura of the original. Image prompt correctly uses "
                    "desaturated teal/amber palette."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Vintage watch campaign scores 8.9 — one of the "
                    "strongest in the Velvet Dispatch persona. The concept of "
                    "continuing a conversation with absent makers is deeply "
                    "aligned with Benjamin's aura thesis. "
                    "Recommendation: SHIP."
                ),
            ),
        ],
    ),
    # ── User 6: Velvet Dispatch × Handmade Ceramics ──
    MockUser(
        persona_name="Velvet Dispatch",
        niche="Handmade ceramics studio",
        verifiable_query="Why does the kiln produce unrepeatable results?",
        expected_marker="wood-fired kiln glaze unpredictability",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for a handmade ceramics studio "
                    "that embraces the wood-fired kiln glaze unpredictability "
                    "as its defining aesthetic. No two pieces emerge the same. "
                    "The studio sees this as the last honest act in a world "
                    "of identical objects."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The kiln decides. The potter proposes a form and "
                    "the fire answers with its own language. Wood-fired kiln "
                    "glaze unpredictability is not a flaw in the method — it is "
                    "the method. Each piece carries the specific temperature, "
                    "the specific ash, the specific hour it was born. "
                    "Reproduction is not difficult. It is impossible.\n\n"
                    "Image Prompt: A row of ceramic bowls with varied ash glazes, "
                    "desaturated teal and amber, soft grain, natural window light "
                    "casting long shadows across a wooden worktable, each bowl "
                    "subtly different in color, 4:5 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.2. The wood-fired kiln glaze "
                    "unpredictability is effectively framed as irreproducibility "
                    "rather than imperfection. The Melancholic tone is present "
                    "in 'the specific hour it was born.' Benjamin's reproduction "
                    "thesis is implied without being cited directly. Image "
                    "prompt uses correct Velvet Dispatch palette."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Ceramics studio campaign scores 8.2. The "
                    "wood-fired kiln narrative aligns well with Velvet Dispatch "
                    "philosophy of mourning the original. The impossibility of "
                    "reproduction is the central claim. Recommendation: SHIP."
                ),
            ),
        ],
    ),
    # ── User 7: Velvet Dispatch × Vinyl Pressing Plant ──
    MockUser(
        persona_name="Velvet Dispatch",
        niche="Vinyl record pressing plant",
        verifiable_query="How is the master disc created from a recording?",
        expected_marker="lacquer master disc cutting lathe",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for a vinyl record pressing plant "
                    "that still uses a lacquer master disc cutting lathe. The "
                    "plant believes the physical groove — carved into lacquer "
                    "by a sapphire stylus — is the last analog link between "
                    "the musician and the listener."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The sapphire touches the lacquer and the sound "
                    "becomes geography. The lacquer master disc cutting lathe "
                    "translates frequency into terrain — ridges and valleys "
                    "measured in microns. The digital file contains the same "
                    "information. It does not contain the same weight. A record "
                    "is heavy because the music is inside it, physically.\n\n"
                    "Image Prompt: Close-up of a cutting lathe stylus carving "
                    "grooves into a spinning lacquer disc, desaturated teal and "
                    "amber, soft grain, reflective surface catching warm light, "
                    "spiral groove visible, 4:5 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.5. The lacquer master disc "
                    "cutting lathe is poetically rendered — 'sound becomes "
                    "geography' is a strong Melancholic image. The "
                    "digital-vs-physical weight contrast avoids being cliché "
                    "by grounding it in literal mass. Image prompt correctly "
                    "uses Velvet Dispatch visual language."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Vinyl pressing campaign scores 8.5. The physical "
                    "materiality of the lacquer master disc cutting process is "
                    "the philosophical anchor — sound as geography, music as "
                    "weight. Strong Velvet Dispatch alignment. "
                    "Recommendation: SHIP."
                ),
            ),
        ],
    ),
    # ── User 8: Ferro Static × Underground Electronic Music ──
    MockUser(
        persona_name="Ferro Static",
        niche="Underground electronic music label",
        verifiable_query="What connects the physical cables to the sound?",
        expected_marker="modular synthesizer patch cables",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for an underground electronic "
                    "music label that fetishizes the modular synthesizer patch "
                    "cables as the physical nervous system of sound. The label "
                    "believes the tangle of cables is the last visible proof "
                    "that electronic music is made by hands."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The cables do not organize themselves. Each "
                    "connection is a decision made with fingers, not algorithms. "
                    "Modular synthesizer patch cables are the circulatory system "
                    "of a sound that the DAW cannot replicate — not because it "
                    "lacks the frequency, but because it lacks the friction. "
                    "The patch is impermanent. Pull one cable and the whole "
                    "architecture collapses. That is the point.\n\n"
                    "Image Prompt: Dense tangle of colorful patch cables against "
                    "a dark modular synth faceplate, neon-lit with electric blue "
                    "and magenta accents, deep blacks, cyberpunk grain, 9:16 "
                    "aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.3. The modular synthesizer "
                    "patch cables as 'circulatory system' is an effective "
                    "Sardonic metaphor. The capitalist realism undertone — "
                    "physical friction vs. digital frictionlessness — aligns "
                    "with Ferro Static philosophy. The deliberate fragility "
                    "of the patch is well observed. Image prompt correctly "
                    "uses neon noir palette."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Electronic music label campaign scores 8.3. "
                    "The modular synthesizer patch cables serve as a metaphor "
                    "for deliberate impermanence in a world of saved presets. "
                    "Sardonic register is consistent. Recommendation: SHIP."
                ),
            ),
        ],
    ),
    # ── User 9: Ferro Static × Cyberpunk Fashion ──
    MockUser(
        persona_name="Ferro Static",
        niche="Cyberpunk fashion atelier",
        verifiable_query="How do technical fabrics reshape the body?",
        expected_marker="techwear gore-tex membrane layering",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for a cyberpunk fashion atelier "
                    "that treats techwear gore-tex membrane layering as a form "
                    "of urban armor. The atelier believes clothing should "
                    "protect the body from the city, not decorate it for the "
                    "city."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The membrane does not breathe for you. It "
                    "negotiates with the atmosphere on your behalf. Techwear "
                    "gore-tex membrane layering is not fashion — it is "
                    "infrastructure. The city produces rain, wind, surveillance, "
                    "and friction. The garment produces a boundary. You are not "
                    "wearing a jacket. You are wearing a policy.\n\n"
                    "Image Prompt: Full-body shot of a figure in matte black "
                    "technical layers, neon-lit from below with electric cyan "
                    "accents, deep blacks, wet pavement reflections, cyberpunk "
                    "grain, urban alley backdrop, 9:16 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.8. The techwear gore-tex "
                    "membrane layering is reframed as 'infrastructure' and "
                    "'policy' — classic Ferro Static Sardonic register. The "
                    "capitalist realism critique is embedded in 'the city "
                    "produces surveillance.' Strong visual-verbal alignment. "
                    "Image prompt is technically precise for neon noir."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Cyberpunk fashion campaign scores 8.8, the "
                    "highest in the Ferro Static batch. Techwear gore-tex "
                    "membrane layering as urban policy is a distinctive "
                    "conceptual angle. The Sardonic tone is sharp without "
                    "being hostile. Recommendation: SHIP."
                ),
            ),
        ],
    ),
    # ── User 10: Ferro Static × Indie Game Dev ──
    MockUser(
        persona_name="Ferro Static",
        niche="Indie game development studio",
        verifiable_query="What happens when pixels are allowed to decay?",
        expected_marker="procedural generation pixel decay",
        node_outputs=[
            MockNodeOutput(
                node_name="user_brief",
                text=(
                    "Create marketing content for an indie game development "
                    "studio that uses procedural generation pixel decay as a "
                    "core mechanic. The studio believes that games should age, "
                    "degrade, and eventually become unplayable — like everything "
                    "else."
                ),
            ),
            MockNodeOutput(
                node_name="creative_worker",
                text=(
                    "Caption: The world loses a row of pixels every hour you "
                    "play. Procedural generation pixel decay is not a bug — it "
                    "is the thesis. The game is a controlled demolition of its "
                    "own assets. Eventually the sky will be gone. Then the "
                    "ground. Then the character. You are not playing a game. "
                    "You are watching an entropy simulation with a controller "
                    "in your hand.\n\n"
                    "Image Prompt: Screenshot-style image of a pixelated game "
                    "landscape with visible corruption and missing tile rows, "
                    "neon-lit glitch artifacts in electric green and magenta, "
                    "deep black voids where terrain has decayed, cyberpunk "
                    "grain, 9:16 aspect ratio"
                ),
            ),
            MockNodeOutput(
                node_name="critic_worker",
                text=(
                    "Grade: PASS. Vibe Score: 8.1. Procedural generation pixel "
                    "decay as 'controlled demolition' is an effective Sardonic "
                    "frame. The hauntology undertone — watching lost futures "
                    "disappear in real time — aligns with Ferro Static. The "
                    "final line about entropy simulation is sharp. Image prompt "
                    "captures the glitch aesthetic within neon noir constraints."
                ),
            ),
            MockNodeOutput(
                node_name="executive_briefing",
                text=(
                    "Summary: Indie game studio campaign scores 8.1. "
                    "Procedural generation pixel decay as entropy metaphor is "
                    "conceptually strong. The game-as-demolition angle is "
                    "distinctive. Minor risk: the concept may be too abstract "
                    "for general gaming audiences. Recommendation: REVIEW."
                ),
            ),
        ],
    ),
]
