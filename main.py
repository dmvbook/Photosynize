import streamlit as st  # Import Streamlit so we can build the app interface.

from plant_api import identify_plant  # Import the PlantNet plant identification function.
from nemotron_api import askplant_question, getplant_info  # Import the AI helper functions for profile and Q&A.


st.set_page_config(page_title="Photosynize", page_icon="🌿", layout="wide")  # Set the app title, icon, and wide layout for the UI.


# Streamlit session state keeps important results across reruns so the user does not lose their plant selection or answers.
for key in [  # Create a list of values we want to keep between reruns.
    "uploaded_image",  # Store the uploaded image object.
    "plant_result",  # Store the raw result from PlantNet.
    "identified_plant_name",  # Store the best matched plant name.
    "plant_profile",  # Store the generated plant profile text.
    "health_analysis",  # Store the health analysis response.
    "follow_up_answer",  # Store the last follow-up answer.
]:
    if key not in st.session_state:  # Only create a value if it does not already exist.
        st.session_state[key] = None  # Give each key an initial None value.


def extract_best_plant_result(raw_result):  # Pull the best plant match out of the PlantNet response.
    """Pull the most useful plant name, scientific name, and confidence from the current PlantNet response."""  # Explain what this helper does.
    if not isinstance(raw_result, dict):  # If the response is not a dictionary, stop early.
        return {}  # Return an empty result so the app can fail gracefully.

    suggestions = raw_result.get("results", [])  # Get the list of PlantNet results from the response.

    if not isinstance(suggestions, list):  # If results is not a list, stop early.
        return {}  # Return an empty result.

    for suggestion in suggestions:  # Loop through each possible plant match.
        if not isinstance(suggestion, dict):  # Skip anything that is not a dictionary.
            continue  # Move to the next result.

        species = suggestion.get("species") or {}  # Get the nested species info dictionary.
        common_names = species.get("commonNames") or []  # Pull the common names array, or empty list if missing.
        scientific_name = species.get("scientificName")  # Pull the scientific name from the species dictionary.
        plant_name = common_names[0] if common_names else None  # Use the first common name when available.
        confidence = suggestion.get("score")  # PlantNet gives the confidence as the score on the outer object.

        if plant_name or scientific_name:  # Only return a match if at least one usable name exists.
            return {  # Return a cleaned, simpler dictionary for the frontend.
                "plant_name": plant_name,  # Store the common name.
                "scientific_name": scientific_name,  # Store the scientific name.
                "confidence": confidence,  # Store the confidence/score.
            }

    return {}  # Return empty if nothing usable is found.


def render_loading_status(label):
    return f"""
    <div class="status-row">
        <span class="loading-spinner" aria-hidden="true"></span>
        <span>{label}</span>
    </div>
    """


def reset_care_routine():
    for task_key in ["care_light", "care_soil", "care_inspect", "care_rotate"]:
        st.session_state[task_key] = False


st.markdown(  # Add custom CSS to improve contrast, spacing, and input styling.
    """
    <style>
    :root {
        --bg-soft: #f4fbf4;
        --bg-page: #eef9ee;
        --card: rgba(255,255,255,0.8);
        --card-strong: #ffffff;
        --line: rgba(22, 96, 66, 0.12);
        --text: #143f2c;
        --muted: #4d6f5f;
        --primary: #2f7d4a;
        --primary-strong: #22653d;
        --primary-soft: #e7f8ea;
        --shadow: 0 18px 40px rgba(32, 85, 58, 0.10);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(140, 205, 145, 0.28), transparent 24%),
            linear-gradient(180deg, var(--bg-page) 0%, var(--bg-soft) 100%);
        color: var(--text);
        font-family: "Inter", "Segoe UI", sans-serif;
    }

    .block-container {
        padding-top: 1.75rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }

    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.85rem;
    }

    h1, h2, h3 {
        color: var(--text);
        letter-spacing: -0.03em;
    }

    h1 {
        font-size: 3rem !important;
        margin-bottom: 0.2rem !important;
    }

    .stCaption {
        color: var(--muted) !important;
        font-size: 1rem !important;
        margin-bottom: 1.25rem !important;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(35, 102, 65, 0.98), rgba(61, 148, 86, 0.90));
        border-radius: 24px;
        padding: 1.3rem 1.4rem 1rem 1.4rem;
        margin-bottom: 1.25rem;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255,255,255,0.12);
    }

    .hero-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin-top: 0.8rem;
    }

    .hero-stat {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
        color: #f7fff8;
    }

    .hero-stat strong {
        display: block;
        font-size: 1.05rem;
        margin-bottom: 0.18rem;
    }

    .hero-tag {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        color: #f1fff4;
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 999px;
        padding: 0.4rem 0.8rem;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .stButton > button {
        background: linear-gradient(180deg, #3d8e60 0%, #2f7d4a 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        min-height: 2.9rem;
        padding: 0.55rem 1.2rem;
        box-shadow: 0 8px 18px rgba(47, 125, 74, 0.18);
        transition: all 0.2s ease;
        opacity: 1;
    }

    .stButton > button:hover {
        background: linear-gradient(180deg, #4aa26c 0%, #357d4f 100%);
        transform: translateY(-1px);
        box-shadow: 0 10px 20px rgba(47, 125, 74, 0.22);
    }

    .stButton > button:focus {
        box-shadow: 0 0 0 3px rgba(47, 125, 74, 0.22);
        outline: none;
    }

    .stSelectbox label,
    .stTextInput label,
    .stTextArea label,
    .stFileUploader label {
        color: var(--text) !important;
        font-weight: 700 !important;
        font-size: 0.96rem !important;
    }

    .stSelectbox div[role="combobox"],
    .stTextInput input,
    .stTextArea textarea,
    .stFileUploader div[data-testid="stFileUploaderDropzone"] {
        background: var(--card-strong) !important;
        color: var(--text) !important;
        border: 1px solid rgba(26, 94, 63, 0.32) !important;
        border-radius: 12px !important;
        box-shadow: inset 0 1px 2px rgba(16, 42, 31, 0.03);
    }

    .stSelectbox div[role="combobox"]:focus-within,
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stFileUploader div[data-testid="stFileUploaderDropzone"]:focus-within {
        border-color: rgba(26, 94, 63, 0.7) !important;
        box-shadow: 0 0 0 3px rgba(47, 125, 74, 0.14) !important;
    }

    .stTextArea textarea {
        min-height: 115px;
    }

    .stForm {
        background: rgba(255,255,255,0.42);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem 1rem 0.4rem 1rem;
        box-shadow: 0 8px 20px rgba(17, 68, 44, 0.04);
    }

    .stAlert {
        border-radius: 14px;
        border: 1px solid transparent;
    }

    .identification-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(47, 125, 74, 0.24);
        border-radius: 14px;
        padding: 0.8rem 1rem;
        margin-top: 0.35rem;
        box-shadow: 0 8px 18px rgba(20, 64, 41, 0.07);
    }

    .identification-status {
        color: var(--primary-strong);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .identification-name {
        color: var(--text);
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.25;
        margin-top: 0.2rem;
    }

    .identification-scientific {
        color: var(--muted);
        font-size: 0.95rem;
        font-style: italic;
        margin-top: 0.1rem;
    }

    .identification-confidence {
        color: var(--muted);
        font-size: 0.84rem;
        font-weight: 600;
        margin-top: 0.45rem;
    }

    .care-routine {
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(47, 125, 74, 0.16);
        border-radius: 16px;
        padding: 1rem 1.1rem 0.55rem 1.1rem;
        box-shadow: 0 8px 18px rgba(20, 64, 41, 0.05);
    }

    .care-routine-kicker {
        color: var(--primary-strong);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .care-routine-title {
        color: var(--text);
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 0.2rem;
    }

    .care-routine-copy {
        color: var(--muted);
        font-size: 0.9rem;
        margin-top: 0.15rem;
    }

    .status-row {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        width: fit-content;
        margin: 0.5rem 0 0.8rem 0;
        padding: 0.7rem 0.9rem;
        border-radius: 12px;
        background: rgba(230, 248, 234, 0.9);
        border: 1px solid rgba(47, 125, 74, 0.18);
        color: var(--text);
        font-weight: 600;
        box-shadow: 0 8px 18px rgba(47, 125, 74, 0.07);
    }

    .loading-spinner {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid rgba(47, 125, 74, 0.18);
        border-top-color: #2f7d4a;
        display: inline-block;
        animation: spin 0.9s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .stSuccess {
        background: rgba(230, 248, 234, 0.9) !important;
        border-color: rgba(47, 125, 74, 0.22) !important;
    }

    .stWarning {
        background: rgba(255, 246, 220, 0.85) !important;
        border-color: rgba(197, 142, 29, 0.25) !important;
    }

    .stInfo {
        background: rgba(235, 245, 255, 0.85) !important;
        border-color: rgba(52, 108, 181, 0.18) !important;
    }

    .profile-shell {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 0.85rem;
        margin-top: 0.9rem;
    }

    .profile-detail,
    .profile-bullet,
    .profile-paragraph {
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(25, 86, 55, 0.10);
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
        box-shadow: 0 8px 18px rgba(20, 64, 41, 0.04);
        color: var(--text);
    }

    .profile-shell .profile-detail {
        width: 100%;
    }

    .profile-detail {
        display: flex;
        flex-direction: column;
        gap: 0.18rem;
    }

    .profile-label {
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted);
        font-weight: 700;
    }

    .profile-value {
        font-weight: 600;
        color: var(--text);
    }

    .profile-bullet {
        color: var(--text);
        font-weight: 500;
    }

    .profile-paragraph {
        grid-column: 1 / -1;
        line-height: 1.6;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 160px;
        border-style: dashed !important;
    }

    [data-testid="stImage"] > img {
        border-radius: 18px;
        box-shadow: 0 8px 18px rgba(15, 51, 32, 0.10);
    }

    .block-container section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.6);
    }

    @media (max-width: 768px) {
        .hero-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,  # Allow the CSS block to render in Streamlit.
)


st.title("Photosynize")  # Show the main app title at the top.
st.caption("Identify your plant, understand its needs, and get AI-powered care recommendations.")  # Add a short subtitle under the title.

st.markdown(
    """
    <div class="hero-card">
      <div class="hero-tag">Plant care companion</div>
      <div class="hero-grid">
        <div class="hero-stat"><strong>1. Identify</strong>Upload a photo and match it to a likely plant species.</div>
        <div class="hero-stat"><strong>2. Learn</strong>Review a tailored care profile and growing needs.</div>
        <div class="hero-stat"><strong>3. Act</strong>Check health issues and ask questions in context.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.subheader("1. Upload a plant image")  # Label the upload section.
plant_upload = st.file_uploader(  # Let the user upload an image file.
    "Upload a JPG, JPEG, or PNG image",  # Visible text describing accepted file types.
    type=["jpg", "jpeg", "png"],  # Only accept JPG, JPEG, and PNG files.
    key="plant_upload",  # Use a stable session key for this uploader.
)

if plant_upload is not None:  # Only run the upload block if a file was chosen.
    st.session_state["uploaded_image"] = plant_upload  # Save the uploaded image in session state.
    st.image(plant_upload, caption=plant_upload.name, use_container_width=True)  # Display the uploaded image to the user.

    identify_submitted = st.button("Identify Plant", key="identify_plant_button")  # Add a button that starts the PlantNet identification.
    identify_loading_placeholder = st.empty()  # Stable placeholder so the loading indicator appears without ghosting.
    identify_message_placeholder = st.empty()  # Stable placeholder for success/error messages.
    identify_result_placeholder = st.empty()  # Stable placeholder for the polished identification card.

    if identify_submitted:  # Only call PlantNet after the user clicks the button.
        identify_result_placeholder.empty()
        identify_loading_placeholder.markdown(
            render_loading_status("Identifying your plant..."),
            unsafe_allow_html=True,
        )
        identify_message_placeholder.empty()

        try:  # Catch failures so the page does not crash.
            result = identify_plant(plant_upload)  # Call the backend PlantNet identification function.
            st.session_state["plant_result"] = result  # Save the raw response in session state.

            best_match = extract_best_plant_result(result)  # Turn the raw response into a cleaner result.
            plant_name = best_match.get("plant_name") or best_match.get("scientific_name")  # Choose the best name to display.
            st.session_state["identified_plant_name"] = plant_name  # Save the chosen plant name.

            if plant_name:  # Only show success UI if we found a valid plant name.
                identify_message_placeholder.empty()
            else:  # If no match is found, tell the user clearly.
                identify_message_placeholder.warning("The plant was uploaded, but no clear match was returned.")  # Show a warning instead of crashing.
        except Exception as exc:  # Catch API or parsing errors.
            identify_message_placeholder.error(f"Plant identification failed. Please try again with a clearer image. Error: {type(exc).__name__}")  # Show a user-friendly error message.
        finally:
            identify_loading_placeholder.empty()

    if st.session_state.get("plant_result") and st.session_state.get("identified_plant_name"):
        best_match = extract_best_plant_result(st.session_state["plant_result"])
        confidence = best_match.get("confidence")
        confidence_text = (
            f"{confidence:.2%} confidence"
            if isinstance(confidence, float)
            else f"{confidence} confidence"
            if confidence is not None
            else "Confidence unavailable"
        )
        scientific_name = best_match.get("scientific_name")
        scientific_markup = (
            f'<div class="identification-scientific">{scientific_name}</div>'
            if scientific_name
            else ""
        )
        identify_result_placeholder.markdown(
            f"""
            <div class="identification-card">
                <div class="identification-status">✓ Plant identified</div>
                <div class="identification-name">{st.session_state["identified_plant_name"]}</div>
                {scientific_markup}
                <div class="identification-confidence">{confidence_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if st.session_state.get("identified_plant_name"):  # Only show the profile section after a plant has been identified.
    st.markdown("---")  # Add a separator line.
    st.subheader("2. Plant care profile")  # Label the profile section.
    profile_submitted = st.button("Generate Plant Care Profile", key="generate_profile_button")  # Add button to generate AI plant profile.
    profile_loading_placeholder = st.empty()
    profile_message_placeholder = st.empty()
    profile_result_placeholder = st.empty()

    if st.session_state.get("plant_profile"):
        with profile_result_placeholder.container():
            profile_display = st.session_state["plant_profile"].replace("<br>", "<br/>")
            st.markdown(profile_display, unsafe_allow_html=True)  # Display the profile text directly so Markdown renders correctly.

    if profile_submitted:  # Only call Nemotron after the user clicks the button.
        profile_result_placeholder.empty()
        profile_loading_placeholder.markdown(
            render_loading_status("Generating the plant care profile..."),
            unsafe_allow_html=True,
        )
        profile_message_placeholder.empty()

        try:  # Catch any API error.
            plant_name = st.session_state["identified_plant_name"]  # Use the current identified plant.
            profile = getplant_info(plant_name)  # Call Nemotron to generate the plant profile.
            st.session_state["plant_profile"] = profile  # Save the generated profile.
            profile_message_placeholder.success("Plant care profile generated.")  # Notify success.
            with profile_result_placeholder.container():
                profile_display = st.session_state["plant_profile"].replace("<br>", "<br/>")
                st.markdown(profile_display, unsafe_allow_html=True)  # Display the profile text directly so Markdown renders correctly.
        except Exception as exc:  # Catch profile generation errors.
            profile_message_placeholder.error(f"The profile could not be generated right now. Please try again. Error: {type(exc).__name__}")  # Show a friendly error.
        finally:
            profile_loading_placeholder.empty()


if st.session_state.get("identified_plant_name"):  # Only show health analysis when a plant is identified.
    st.markdown("---")
    st.markdown(
        """
        <div class="care-routine">
            <div class="care-routine-kicker">A small ritual for your plant</div>
            <div class="care-routine-title">Today's care routine</div>
            <div class="care-routine-copy">Turn advice into a few concrete actions and keep the plant moving in the right direction.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    routine_columns = st.columns(4)
    routine_tasks = [
        ("care_light", "Check the light", "Is the plant getting the right exposure?"),
        ("care_soil", "Feel the soil", "Water only if the top layer is dry."),
        ("care_inspect", "Inspect the leaves", "Look for spots, pests, or new growth."),
        ("care_rotate", "Rotate the pot", "Give growth a more even chance."),
    ]
    completed_tasks = 0
    for routine_column, (task_key, task_title, task_help) in zip(routine_columns, routine_tasks):
        with routine_column:
            if st.checkbox(task_title, key=task_key, help=task_help):
                completed_tasks += 1

    progress_column, reset_column = st.columns([5, 1])
    with progress_column:
        st.progress(completed_tasks / len(routine_tasks), text=f"{completed_tasks} of {len(routine_tasks)} care steps complete")
    with reset_column:
        st.button("Reset routine", key="reset_care_routine", on_click=reset_care_routine)

    st.markdown("---")  # Add a separator.
    st.subheader("3. Plant health analysis")  # Label the health analysis section.
    health_loading_placeholder = st.empty()
    health_message_placeholder = st.empty()
    health_result_placeholder = st.empty()

    if st.session_state.get("health_analysis"):
        with health_result_placeholder.container():
            st.markdown("### Plant Health Analysis")  # Heading for the analysis response.
            health_display = st.session_state["health_analysis"].replace("<br>", "<br/>")
            st.markdown(health_display, unsafe_allow_html=True)  # Display the analysis text with the same formatting as the plant profile.

    with st.form("health_analysis_form"):  # Use a form so the user can submit all inputs together.
        # These inputs create a structured health prompt so Nemotron can reason over the plant's conditions.
        col1, col2 = st.columns(2)  # Place the fields in two columns on wide screens to reduce vertical height.

        with col1:
            light_level = st.selectbox("Light level", ["Low", "Medium", "Bright"])  # Let user choose light exposure.
            watering_frequency = st.selectbox(  # Let user choose how often the plant is watered.
                "Watering frequency",
                ["Daily", "Every few days", "Weekly", "Every two weeks", "Rarely"],
            )
            environment = st.selectbox("Environment", ["Indoor", "Outdoor"])  # Choose where the plant is growing.

        with col2:
            leaf_condition = st.selectbox("Leaf condition", ["Healthy", "Yellow", "Brown", "Drooping", "Spots"])  # Select leaf health status.
            soil_condition = st.selectbox("Soil condition", ["Wet", "Moist", "Dry"])  # Choose soil moisture state.
            symptoms = st.text_area(  # Let the user add extra observations.
                "Additional symptoms or observations",
                placeholder="Examples: leaves curling, white spots, insects, slow growth, recently repotted",
            )

        submitted = st.form_submit_button("Analyze Plant Health")  # Submit the health information.

    if submitted:  # Only run the analysis when the user clicks submit.
        health_result_placeholder.empty()
        health_loading_placeholder.markdown(
            render_loading_status("Analyzing plant health..."),
            unsafe_allow_html=True,
        )
        health_message_placeholder.empty()

        plant_name = st.session_state["identified_plant_name"]  # Use the selected plant name.
        question = (  # Build one clear prompt for the AI analysis.
            f"Analyze the health of a {plant_name}. "  # Add the plant name to the prompt.
            f"Light level: {light_level}. "  # Include light condition.
            f"Watering frequency: {watering_frequency}. "  # Include watering pattern.
            f"Leaf condition: {leaf_condition}. "  # Add leaf condition.
            f"Soil condition: {soil_condition}. "  # Add soil status.
            f"Environment: {environment}. "  # Include environment type.
            f"Additional symptoms or observations: {symptoms or 'None provided'}. "  # Add any extra symptoms.
            "Return: likely issue, risk level (Low / Moderate / High), reasoning based on the supplied conditions, recommended actions, urgency, and anything that cannot be determined reliably."  # Ask for structured output.
        )

        try:  # Catch health-analysis errors.
            analysis = askplant_question(plant_name, question)  # Send the structured question to Nemotron.
            st.session_state["health_analysis"] = analysis  # Save the answer.
            with health_result_placeholder.container():
                st.markdown("### Plant Health Analysis")  # Heading for the analysis response.
                health_display = st.session_state["health_analysis"].replace("<br>", "<br/>")
                st.markdown(health_display, unsafe_allow_html=True)  # Display the analysis text with the same formatting as the plant profile.
        except Exception as exc:  # Catch any error from the AI call.
            health_message_placeholder.error(f"Plant health analysis failed. Please try again. Error: {type(exc).__name__}")  # Show error to the user.
        finally:
            health_loading_placeholder.empty()


if st.session_state.get("identified_plant_name"):  # Only show the Q&A area for an identified plant.
    st.markdown("---")  # Add a divider.
    st.subheader("4. Ask Photosynize")  # Label the follow-up Q&A section.
    question_loading_placeholder = st.empty()
    question_message_placeholder = st.empty()
    question_result_placeholder = st.empty()

    if st.session_state.get("follow_up_answer"):
        with question_result_placeholder.container():
            st.markdown("### Follow-up answer")  # Heading for the answer.
            st.markdown(st.session_state["follow_up_answer"])  # Display the latest answer.

    with st.form("follow_up_form"):  # Use a form for clean follow-up submissions.
        # This keeps the follow-up chat flow focused on the currently identified plant.
        col_input, col_button = st.columns([5, 1])  # Keep the question box and Ask button close together.

        with col_input:
            follow_up_question = st.text_input(  # Let the user ask a custom question.
                "Ask a question about this plant",
                placeholder="Example: Why are the leaves yellow?",
                key="follow_up_input",
            )

        with col_button:
            ask_submitted = st.form_submit_button("Ask")  # Submit the question.

    if ask_submitted and follow_up_question:  # Only ask if the user typed a question.
        question_result_placeholder.empty()
        question_loading_placeholder.markdown(
            render_loading_status("Thinking..."),
            unsafe_allow_html=True,
        )
        question_message_placeholder.empty()

        try:  # Catch follow-up API errors.
            answer = askplant_question(st.session_state["identified_plant_name"], follow_up_question)  # Ask the AI about the plant.
            st.session_state["follow_up_answer"] = answer  # Save the answer.
            question_message_placeholder.success("Answer ready.")  # Confirm the answer is ready.
            with question_result_placeholder.container():
                st.markdown("### Follow-up answer")  # Heading for the answer.
                st.markdown(st.session_state["follow_up_answer"])  # Display the answer text.
        except Exception as exc:  # Catch errors during Q&A.
            question_message_placeholder.error(f"The follow-up question could not be answered. Please try again. Error: {type(exc).__name__}")  # Show the user the error.
        finally:
            question_loading_placeholder.empty()


if not st.session_state.get("identified_plant_name"):  # If no plant is identified yet, show a helpful prompt.
    st.info("Upload a plant photo and identify it to unlock the care profile, plant health analysis, and follow-up questions.")  # Tell the user the next step.
