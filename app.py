
import streamlit as st
import pandas as pd
import random

st.set_page_config(
    page_title="TV Program Scheduling using GA",
    layout="wide"
)

# -----------------------------
# CONSTANTS
# -----------------------------
POP_SIZE = 50
GENERATIONS = 100
ELITISM_SIZE = 2

HOURS = [f"{h:02d}:00" for h in range(6, 24)]

# -----------------------------
# LOAD CSV
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_csv("ratings.csv")

try:
    df = load_data()
    programs = df["Program"].astype(str).tolist()
    ratings = df[HOURS].astype(float).values

except Exception as e:
    st.error(f"Unable to load ratings.csv: {e}")
    st.stop()

if df.empty or len(programs) < 2:
    st.error("The CSV must contain at least two programmes.")
    st.stop()

if ratings.shape != (len(programs), len(HOURS)):
    st.error("Invalid rating dataset dimensions.")
    st.stop()

if not pd.notna(ratings).all() or (ratings < 0).any() or (ratings > 1).any():
    st.error("Ratings must be complete and between 0 and 1.")
    st.stop()

# -----------------------------
# STUDENT INFORMATION
# -----------------------------
st.sidebar.header("Student Information")

student_name = st.sidebar.text_input(
    "Student Name",
    ""
)

matric_number = st.sidebar.text_input(
    "Matric Number",
    ""
)

st.sidebar.divider()

# -----------------------------
# RANDOM SEED
# -----------------------------
st.sidebar.header("Genetic Algorithm")

seed = st.sidebar.number_input(
    "Random seed (same seed = repeatable results)",
    min_value=0,
    value=42,
    step=1
)

st.sidebar.write(
    f"GEN = {GENERATIONS}, POP = {POP_SIZE}, EL_S = {ELITISM_SIZE}"
)

# -----------------------------
# GENETIC ALGORITHM
# -----------------------------
def fitness(schedule):
    return sum(
        ratings[program_index, slot]
        for slot, program_index in enumerate(schedule)
    )


def create_schedule(rng):
    return [
        rng.randrange(len(programs))
        for _ in HOURS
    ]


def crossover(parent1, parent2, rng):
    point = rng.randint(1, len(HOURS) - 1)

    return (
        parent1[:point] +
        parent2[point:]
    )


def mutate(schedule, mutation_rate, rng):
    child = schedule.copy()

    for i in range(len(child)):
        if rng.random() < mutation_rate:
            choices = [
                p for p in range(len(programs))
                if p != child[i]
            ]

            child[i] = rng.choice(choices)

    return child


def genetic_algorithm(cr, mr, random_seed):

    rng = random.Random(random_seed)

    population = [
        create_schedule(rng)
        for _ in range(POP_SIZE)
    ]

    for generation in range(GENERATIONS):

        population.sort(
            key=fitness,
            reverse=True
        )

        new_population = population[:ELITISM_SIZE]

        while len(new_population) < POP_SIZE:

            parent1 = rng.choice(population[:20])
            parent2 = rng.choice(population[:20])

            if rng.random() < cr:
                child = crossover(
                    parent1,
                    parent2,
                    rng
                )
            else:
                child = parent1.copy()

            child = mutate(child, mr, rng)

            new_population.append(child)

        population = new_population

    population.sort(
        key=fitness,
        reverse=True
    )

    best = population[0]

    return best, fitness(best)


# -----------------------------
# SESSION STATE
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "results" not in st.session_state:
    st.session_state.results = {}


# -----------------------------
# RUN TRIAL FUNCTION
# -----------------------------
def run_trial(trial_name, cr, mr):

    best, score = genetic_algorithm(
        cr,
        mr,
        int(seed)
    )

    schedule_rows = []

    for slot, program_index in enumerate(best):

        schedule_rows.append({
            "Time Slot": HOURS[slot],
            "Program": programs[program_index],
            "Rating": round(
                float(ratings[program_index, slot]), 2
            )
        })

    result = {
        "Trial": trial_name,
        "CO_R": cr,
        "MUT_R": mr,
        "Total Ratings": round(score, 2)
    }

    # Avoid duplicate trial records
    st.session_state.history = [
        item for item in st.session_state.history
        if item["Trial"] != trial_name
    ]

    st.session_state.history.append(result)

    st.session_state.results[trial_name] = {
        "summary": result,
        "schedule": schedule_rows
    }


# -----------------------------
# MAIN INTERFACE
# -----------------------------
st.title("TV Program Scheduling using a Genetic Algorithm")

if student_name or matric_number:
    st.caption(
        f"Prepared by: {student_name} | Matric Number: {matric_number}"
    )

st.divider()

# -----------------------------
# FOUR TRIAL TABS
# -----------------------------
tab_default, tab1, tab2, tab3 = st.tabs([
    "Default",
    "Trial 1",
    "Trial 2",
    "Trial 3"
])


# -----------------------------
# DEFAULT
# -----------------------------
with tab_default:

    st.write(
        "CO_R = 0.8, MUT_R = 0.2 (default values from the assignment)"
    )

    cr = st.slider(
        "CO_R (Crossover Rate)",
        0.0, 0.95, 0.80, 0.05,
        key="co_default"
    )

    mr = st.slider(
        "MUT_R (Mutation Rate)",
        0.01, 0.20, 0.20, 0.01,
        key="mut_default"
    )

    if st.button("Run Default", key="run_default"):
        run_trial("Default", cr, mr)

    if "Default" in st.session_state.results:

        result = st.session_state.results["Default"]

        st.success(
            f"Total Ratings = {result['summary']['Total Ratings']:.2f}"
        )

        st.subheader("Generated TV Schedule")

        st.dataframe(
            pd.DataFrame(result["schedule"]),
            use_container_width=True,
            hide_index=True
        )


# -----------------------------
# TRIAL 1
# -----------------------------
with tab1:

    cr = st.slider(
        "CO_R (Crossover Rate)",
        0.0, 0.95, 0.95, 0.05,
        key="co_trial1"
    )

    mr = st.slider(
        "MUT_R (Mutation Rate)",
        0.01, 0.05, 0.05, 0.01,
        key="mut_trial1"
    )

    if st.button("Run Trial 1", key="run_trial1"):
        run_trial("Trial 1", cr, mr)

    if "Trial 1" in st.session_state.results:

        result = st.session_state.results["Trial 1"]

        st.success(
            f"Total Ratings = {result['summary']['Total Ratings']:.2f}"
        )

        st.subheader("Generated TV Schedule")

        st.dataframe(
            pd.DataFrame(result["schedule"]),
            use_container_width=True,
            hide_index=True
        )


# -----------------------------
# TRIAL 2
# -----------------------------
with tab2:

    cr = st.slider(
        "CO_R (Crossover Rate)",
        0.0, 0.95, 0.50, 0.05,
        key="co_trial2"
    )

    mr = st.slider(
        "MUT_R (Mutation Rate)",
        0.01, 0.05, 0.03, 0.01,
        key="mut_trial2"
    )

    if st.button("Run Trial 2", key="run_trial2"):
        run_trial("Trial 2", cr, mr)

    if "Trial 2" in st.session_state.results:

        result = st.session_state.results["Trial 2"]

        st.success(
            f"Total Ratings = {result['summary']['Total Ratings']:.2f}"
        )

        st.subheader("Generated TV Schedule")

        st.dataframe(
            pd.DataFrame(result["schedule"]),
            use_container_width=True,
            hide_index=True
        )


# -----------------------------
# TRIAL 3
# -----------------------------
with tab3:

    cr = st.slider(
        "CO_R (Crossover Rate)",
        0.0, 0.95, 0.95, 0.05,
        key="co_trial3"
    )

    mr = st.slider(
        "MUT_R (Mutation Rate)",
        0.01, 0.05, 0.01, 0.01,
        key="mut_trial3"
    )

    if st.button("Run Trial 3", key="run_trial3"):
        run_trial("Trial 3", cr, mr)

    if "Trial 3" in st.session_state.results:

        result = st.session_state.results["Trial 3"]

        st.success(
            f"Total Ratings = {result['summary']['Total Ratings']:.2f}"
        )

        st.subheader("Generated TV Schedule")

        st.dataframe(
            pd.DataFrame(result["schedule"]),
            use_container_width=True,
            hide_index=True
        )


# -----------------------------
# HISTORY
# -----------------------------
st.divider()

st.header("History (all runs)")

if st.session_state.history:

    history_df = pd.DataFrame(
        st.session_state.history
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = history_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download History (CSV)",
        data=csv_data,
        file_name="trial_history.csv",
        mime="text/csv"
    )

    if st.button("Clear History"):
        st.session_state.history = []
        st.session_state.results = {}
        st.rerun()

else:
    st.info("No runs yet. Press a Run button to start.")


# -----------------------------
# DATASET PREVIEW
# -----------------------------
with st.expander("View Rating Dataset"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
