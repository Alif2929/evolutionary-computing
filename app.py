import io
import random
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TV Program Scheduling using GA",
    page_icon="📺",
    layout="wide",
)

# -------------------- CONSTANTS --------------------
HOUR_NUMBERS = list(range(6, 24))
CSV_HOURS = [f"Hour {hour}" for hour in HOUR_NUMBERS]
DISPLAY_HOURS = [f"{hour:02d}:00" for hour in HOUR_NUMBERS]
POP_SIZE = 50
GENERATIONS = 100
ELITISM_SIZE = 2
PARENT_POOL_SIZE = 20
TRIAL_ORDER = ["Default", "Trial 1", "Trial 2", "Trial 3"]

# -------------------- LOAD LECTURER CSV --------------------
@st.cache_data
def read_rating_csv(file_bytes):
    return pd.read_csv(io.BytesIO(file_bytes))

try:
    csv_bytes = Path("ratings.csv").read_bytes()
    rating_df = read_rating_csv(csv_bytes)
except Exception as error:
    st.error(f"Unable to read ratings.csv: {error}")
    st.stop()

required_columns = ["Type of Program"] + CSV_HOURS
missing_columns = [c for c in required_columns if c not in rating_df.columns]
if missing_columns:
    st.error("Missing CSV columns: " + ", ".join(missing_columns))
    st.stop()

rating_df = rating_df[required_columns].copy()
rating_df["Type of Program"] = rating_df["Type of Program"].astype(str).str.strip()
if rating_df.empty or rating_df["Type of Program"].eq("").any():
    st.error("The CSV must contain programme names.")
    st.stop()

numeric_ratings = rating_df[CSV_HOURS].apply(pd.to_numeric, errors="coerce")
if numeric_ratings.isna().any().any():
    st.error("The CSV contains missing or non-numeric rating values.")
    st.stop()
if ((numeric_ratings < 0) | (numeric_ratings > 1)).any().any():
    st.error("All ratings must be between 0 and 1.")
    st.stop()
if len(rating_df) < 2:
    st.error("At least two programmes are required.")
    st.stop()

programs = rating_df["Type of Program"].tolist()
ratings = numeric_ratings.to_numpy(dtype=float)

# -------------------- STUDENT DETAILS --------------------
st.title("TV Program Scheduling using Genetic Algorithm")
st.caption("JIE42903 – Evolutionary Computing")
name_col, matric_col = st.columns(2)
with name_col:
    student_name = st.text_input("Student Name")
with matric_col:
    matric_number = st.text_input("Matric Number")
st.caption(f"Prepared by: {student_name or 'Not entered'} | Matric Number: {matric_number or 'Not entered'}")

# -------------------- SIDEBAR SETTINGS --------------------
st.sidebar.header("Genetic Algorithm Settings")
seed = st.sidebar.number_input("Random Seed", min_value=0, value=42, step=1)
st.sidebar.markdown(f"**GEN** = {GENERATIONS}")
st.sidebar.markdown(f"**POP** = {POP_SIZE}")
st.sidebar.markdown(f"**EL_S** = {ELITISM_SIZE}")
st.sidebar.caption("GEN = Generations | POP = Population Size | EL_S = Elitism Size")

# -------------------- GENETIC ALGORITHM --------------------
def fitness(schedule):
    return sum(ratings[program_index, slot] for slot, program_index in enumerate(schedule))


def create_schedule(rng):
    return [rng.randrange(len(programs)) for _ in HOUR_NUMBERS]


def single_point_crossover(parent1, parent2, rng):
    point = rng.randint(1, len(HOUR_NUMBERS) - 1)
    return parent1[:point] + parent2[point:]


def random_replacement_mutation(schedule, mutation_rate, rng):
    child = schedule.copy()
    for slot in range(len(child)):
        if rng.random() < mutation_rate:
            alternatives = [p for p in range(len(programs)) if p != child[slot]]
            child[slot] = rng.choice(alternatives)
    return child


def genetic_algorithm(crossover_rate, mutation_rate, random_seed):
    rng = random.Random(random_seed)
    population = [create_schedule(rng) for _ in range(POP_SIZE)]

    for _ in range(GENERATIONS):
        population.sort(key=fitness, reverse=True)
        next_population = population[:ELITISM_SIZE]

        while len(next_population) < POP_SIZE:
            parent1 = rng.choice(population[:PARENT_POOL_SIZE])
            parent2 = rng.choice(population[:PARENT_POOL_SIZE])
            if rng.random() < crossover_rate:
                child = single_point_crossover(parent1, parent2, rng)
            else:
                child = parent1.copy()
            child = random_replacement_mutation(child, mutation_rate, rng)
            next_population.append(child)

        population = next_population

    population.sort(key=fitness, reverse=True)
    best = population[0]
    return best, fitness(best)


# -------------------- SAVE TRIAL RESULTS --------------------
if "trial_results" not in st.session_state:
    st.session_state.trial_results = {}


def run_trial(trial_name, crossover_rate, mutation_rate):
    best, score = genetic_algorithm(crossover_rate, mutation_rate, int(seed))
    schedule = [
        {
            "Time Slot": DISPLAY_HOURS[slot],
            "Type of Program": programs[program_index],
            "Rating": round(float(ratings[program_index, slot]), 2),
        }
        for slot, program_index in enumerate(best)
    ]
    summary = {
        "Trial": trial_name,
        "CO_R": round(float(crossover_rate), 2),
        "MUT_R": round(float(mutation_rate), 2),
        "Total Ratings": round(float(score), 2),
    }
    # Store one latest result per trial, avoiding duplicate history rows.
    st.session_state.trial_results[trial_name] = {
        "summary": summary,
        "schedule": schedule,
    }


def show_trial(tab, trial_name, default_co, default_mut, mutation_max):
    with tab:
        st.subheader(f"{trial_name} Parameters")
        col1, col2 = st.columns(2)
        with col1:
            co_rate = st.slider(
                "CO_R (Crossover Rate)", 0.0, 0.95, default_co, 0.05,
                key=f"co_{trial_name.replace(' ', '_').lower()}",
            )
        with col2:
            mut_rate = st.slider(
                "MUT_R (Mutation Rate)", 0.01, mutation_max, default_mut, 0.01,
                key=f"mut_{trial_name.replace(' ', '_').lower()}",
            )

        if st.button(f"Run {trial_name}", key=f"run_{trial_name.replace(' ', '_').lower()}"):
            run_trial(trial_name, co_rate, mut_rate)

        if trial_name in st.session_state.trial_results:
            result = st.session_state.trial_results[trial_name]
            st.success(f"{trial_name} completed | Total Ratings = {result['summary']['Total Ratings']:.2f}")
            st.subheader(f"Generated TV Schedule – {trial_name}")
            st.dataframe(pd.DataFrame(result["schedule"]), use_container_width=True, hide_index=True)


# -------------------- FOUR EXPERIMENT TABS --------------------
st.divider()
tab_default, tab1, tab2, tab3 = st.tabs(["Default", "Trial 1", "Trial 2", "Trial 3"])

# Assignment page 1 gives default MUT_R = 0.20; page 2 gives trial range 0.01–0.05.
show_trial(tab_default, "Default", 0.80, 0.20, 0.20)
show_trial(tab1, "Trial 1", 0.95, 0.05, 0.05)
show_trial(tab2, "Trial 2", 0.50, 0.03, 0.05)
show_trial(tab3, "Trial 3", 0.95, 0.01, 0.05)

# -------------------- HISTORY OF ALL RUNS --------------------
st.divider()


# -------------------- HISTORY OF ALL RUNS --------------------
st.header("History (all runs)")

if st.session_state.trial_results:

    history_rows = [
        st.session_state.trial_results[trial]["summary"]
        for trial in TRIAL_ORDER
        if trial in st.session_state.trial_results
    ]

    history_df = pd.DataFrame(history_rows)

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
        st.session_state.trial_results = {}
        st.rerun()

else:
    st.info("No runs yet. Run an experiment to see the results.")

# -------------------- RATING DATASET --------------------
with st.expander("View Modified Rating Dataset"):

    st.dataframe(
        rating_df,
        use_container_width=True,
        hide_index=True
    )
