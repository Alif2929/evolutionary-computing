
import streamlit as st
import random
import csv
import io
from collections import Counter

st.set_page_config(
    page_title="Evolutionary Computing",
    layout="wide"
)

st.title("Evolutionary Computing")
st.subheader("Genetic Algorithm - TV Scheduling")

name = st.text_input("Student Name", "Alif2929")
matric = st.text_input("Matric Number", "")

st.write("Course: JIE42903 - Evolutionary Computing")
st.write("Prepared by:", name)
st.write("Matric Number:", matric)

st.divider()

programs = {
    "music_program": 0.3,
    "reality_show": 0.4,
    "news": 0.5,
    "documentary": 0.4,
    "tv_series_a": 0.5,
    "movie_a": 0.5,
    "live_soccer": 0.6,
    "movie_b": 0.5,
    "tv_series_b": 0.6,
    "Boxing": 0.1
}

hours = list(range(6, 24))
names = list(programs.keys())

def create_schedule():
    return [random.choice(names) for _ in hours]

def fitness(schedule):
    total = sum(programs[p] for p in schedule)
    counts = Counter(schedule)
    penalty = sum(
        max(0, count - 3) * 0.4
        for count in counts.values()
    )
    return round(total - penalty, 2)

def crossover(parent1, parent2):
    point = random.randint(1, len(hours) - 1)
    return parent1[:point] + parent2[point:]

def mutate(schedule, rate):
    child = schedule.copy()
    for i in range(len(child)):
        if random.random() < rate:
            child[i] = random.choice(names)
    return child

def genetic_algorithm(cr, mr, seed):
    random.seed(seed)
    population = [create_schedule() for _ in range(50)]

    for generation in range(100):
        population.sort(key=fitness, reverse=True)
        new_population = population[:2]

        while len(new_population) < 50:
            parent1, parent2 = random.sample(
                population[:20], 2
            )

            if random.random() < cr:
                child = crossover(parent1, parent2)
            else:
                child = parent1.copy()

            child = mutate(child, mr)
            new_population.append(child)

        population = new_population

    best = max(population, key=fitness)
    return best, fitness(best)

settings = {
    "Default": (0.80, 0.20),
    "Trial 1": (0.95, 0.05),
    "Trial 2": (0.50, 0.03),
    "Trial 3": (0.95, 0.01)
}

st.header("Genetic Algorithm Settings")

trial = st.selectbox(
    "Select Trial",
    list(settings.keys())
)

cr, mr = settings[trial]

st.write("Crossover Rate:", cr)
st.write("Mutation Rate:", mr)
st.write("Population Size: 50")
st.write("Generations: 100")

seed = st.number_input(
    "Random Seed",
    min_value=0,
    value=42,
    step=1
)

if "history" not in st.session_state:
    st.session_state.history = []

if "schedule" not in st.session_state:
    st.session_state.schedule = None

if st.button("Run Genetic Algorithm"):
    best, score = genetic_algorithm(cr, mr, int(seed))

    st.session_state.schedule = best
    st.session_state.score = score
    st.session_state.current_trial = trial

    st.session_state.history.append({
        "Trial": trial,
        "CO_R": cr,
        "MUT_R": mr,
        "Total Ratings": score
    })

if st.session_state.schedule is not None:
    st.success(
        f"{st.session_state.current_trial} | "
        f"Total Ratings = {st.session_state.score:.2f}"
    )

    rows = []

    for hour, program in zip(
        hours, st.session_state.schedule
    ):
        rows.append({
            "Time Slot": f"{hour:02d}:00",
            "Program": program,
            "Rating": programs[program]
        })

    st.subheader("Generated TV Schedule")
    st.dataframe(rows, use_container_width=True)

st.divider()
st.header("Trial Comparison Summary")

if st.session_state.history:
    st.dataframe(
        st.session_state.history,
        use_container_width=True
    )

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "Trial", "CO_R", "MUT_R", "Total Ratings"
        ]
    )
    writer.writeheader()
    writer.writerows(st.session_state.history)

    st.download_button(
        "Download History (CSV)",
        data=output.getvalue(),
        file_name="trial_history.csv",
        mime="text/csv"
    )

    if st.button("Clear History"):
        st.session_state.history = []
        st.session_state.schedule = None
        st.rerun()
else:
    st.info("Run a trial to see the results.")
