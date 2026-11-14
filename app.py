
import streamlit as st
import pandas as pd
import random
import io

st.set_page_config(
    page_title="Evolutionary Computing",
    layout="wide"
)

st.title("Evolutionary Computing")
st.subheader("Genetic Algorithm - TV Scheduling")

# Student information
name = st.text_input("Student Name", "")
matric = st.text_input("Matric Number", "")

st.write("Course: JIE42903 - Evolutionary Computing")
st.write("Prepared by:", name)
st.write("Matric Number:", matric)

st.divider()

# Load rating data from CSV
@st.cache_data
def load_data():
    return pd.read_csv("ratings.csv")

try:
    df = load_data()
except Exception as e:
    st.error(f"Unable to load ratings.csv: {e}")
    st.stop()

if "Program" not in df.columns:
    st.error("CSV must contain a Program column.")
    st.stop()

hours = [f"{h:02d}:00" for h in range(6, 24)]

missing = [h for h in hours if h not in df.columns]

if missing:
    st.error(f"Missing time columns: {missing}")
    st.stop()

if df.empty or df["Program"].isna().any():
    st.error("CSV contains missing program data.")
    st.stop()

programs = df["Program"].astype(str).tolist()
ratings = df[hours].astype(float).values

if (ratings < 0).any() or (ratings > 1).any():
    st.error("Ratings must be between 0 and 1.")
    st.stop()

# Genetic Algorithm
def fitness(schedule):
    return sum(
        ratings[program_index, slot]
        for slot, program_index in enumerate(schedule)
    )

def create_schedule(rng):
    return [
        rng.randrange(len(programs))
        for _ in hours
    ]

def crossover(parent1, parent2, rng):
    point = rng.randint(1, len(hours) - 1)

    child = (
        parent1[:point] +
        parent2[point:]
    )

    return child

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

def genetic_algorithm(cr, mr, seed):

    rng = random.Random(seed)

    population_size = 50
    generations = 100
    elitism = 2

    population = [
        create_schedule(rng)
        for _ in range(population_size)
    ]

    for generation in range(generations):

        population.sort(
            key=fitness,
            reverse=True
        )

        new_population = population[:elitism]

        while len(new_population) < population_size:

            # Select parents from top 20
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

# Trial history
if "history" not in st.session_state:
    st.session_state.history = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

# Interface
st.header("Genetic Algorithm Settings")

trial_name = st.text_input(
    "Trial Name",
    value="Default"
)

col1, col2 = st.columns(2)

with col1:
    cr = st.slider(
        "Crossover Rate (CO_R)",
        min_value=0.0,
        max_value=0.95,
        value=0.80,
        step=0.05
    )

with col2:
    mr = st.number_input(
        "Mutation Rate (MUT_R)",
        min_value=0.01,
        max_value=0.20,
        value=0.20,
        step=0.01,
        format="%.2f"
    )

st.caption(
    "Assignment note: Default MUT_R is 0.20 "
    "on page 1, while page 2 specifies an "
    "experimental range of 0.01 to 0.05. "
    "The trial values can follow the latter range."
)

st.write("Population Size: 50")
st.write("Generations: 100")
st.write("Elitism: 2")

seed = st.number_input(
    "Random Seed",
    min_value=0,
    value=42,
    step=1
)

if st.button("Run Genetic Algorithm"):

    best, score = genetic_algorithm(
        cr,
        mr,
        int(seed)
    )

    schedule_rows = []

    for slot, program_index in enumerate(best):

        schedule_rows.append({
            "Time Slot": hours[slot],
            "Program": programs[program_index],
            "Rating": ratings[program_index, slot]
        })

    result = {
        "Trial": trial_name,
        "CO_R": cr,
        "MUT_R": mr,
        "Total Ratings": round(score, 2)
    }

    # Replace an existing trial with the same name
    st.session_state.history = [
        item for item in st.session_state.history
        if item["Trial"] != trial_name
    ]

    st.session_state.history.append(result)

    st.session_state.current_result = {
        "summary": result,
        "schedule": schedule_rows
    }

# Display schedule
if st.session_state.current_result is not None:

    current = st.session_state.current_result

    st.success(
        f"{current['summary']['Trial']} | "
        f"Total Ratings = "
        f"{current['summary']['Total Ratings']:.2f}"
    )

    st.subheader("Generated TV Schedule")

    st.dataframe(
        pd.DataFrame(current["schedule"]),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# Comparison
st.header("Trial Comparison Summary")

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
        st.session_state.current_result = None
        st.rerun()

else:
    st.info("Run a trial to see the results.")

# Dataset preview
with st.expander("View Rating Dataset"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
