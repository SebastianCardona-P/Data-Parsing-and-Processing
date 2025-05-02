import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
import re
import os
from scipy.stats import norm
import seaborn as sns

# Set random seed for reproducibility
np.random.seed(42)

# Define dtypes to reduce memory usage
DTYPES = {
    "ID_Paciente": "category",
    "Nombre": "object",
    "Género": "category",
    "Edad": "int32",
    "Peso (kg)": "float32",
    "Altura (cm)": "int32",
    "IMC": "float32",
    "Presión Arterial": "object",
    "Síntomas": "object",
    "Diagnóstico (CIE-10)": "category",
    "Enfermedades Crónicas": "object",
    "Fecha Consulta": "object",
    "Hospital": "category",
    "Dirección Hospital": "object",
    "Localidad": "category",
    "Nivel Socioeconómico": "category",
    "Seguro Médico": "category",
}


def parse_blood_pressure(bp):
    """Parse blood pressure string into systolic and diastolic values."""
    if not isinstance(bp, str) or not re.match(r"^\d+/\d+\s*mmHg$", bp):
        return np.nan, np.nan
    try:
        systolic, diastolic = map(int, bp.split(" mmHg")[0].split("/"))
        return systolic, diastolic
    except (ValueError, TypeError):
        return np.nan, np.nan


def calculate_bmi_category(imc):
    """Categorize BMI into Underweight, Normal, Overweight, or Obese."""
    if pd.isna(imc):
        return "Unknown"
    if imc < 18.5:
        return "Underweight"
    elif 18.5 <= imc < 25:
        return "Normal"
    elif 25 <= imc < 30:
        return "Overweight"
    else:
        return "Obese"


def get_age_group(age):
    """Categorize age into <18, 18-60, or >60."""
    if pd.isna(age):
        return "Unknown"
    if age < 18:
        return "<18"
    elif 18 <= age <= 60:
        return "18-60"
    else:
        return ">60"


def clean_and_validate_data(df):
    """Clean and validate the dataset, detecting errors."""
    df = df.copy()

    # Remove empty rows and strip column names
    df = df.dropna(how="all")
    df.columns = [col.strip().replace('"', "") for col in df.columns]

    # Convert numeric columns
    numeric_columns = ["Edad", "Peso (kg)", "Altura (cm)", "IMC"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse blood pressure
    df["Systolic"], df["Diastolic"] = zip(
        *df["Presión Arterial"].apply(parse_blood_pressure)
    )

    # Parse date
    df["Fecha Consulta"] = pd.to_datetime(df["Fecha Consulta"], errors="coerce")

    # Clean symptoms and chronic diseases
    df["Síntomas"] = df["Síntomas"].fillna("Ninguno").str.strip().str.split(", ")
    df["Enfermedades Crónicas"] = (
        df["Enfermedades Crónicas"].fillna("Ninguna").str.strip().str.split(", ")
    )

    # Validate data
    df["Weight_Error"] = (df["Peso (kg)"] < 20) | (df["Peso (kg)"] > 150)
    df["BMI_Error"] = (df["IMC"] < 10) | (df["IMC"] > 50)
    df["Age_Error"] = (df["Edad"] < 0) | (df["Edad"] > 120)
    df["Expected_Systolic"] = 110 + (df["Edad"] / 30) + (df["IMC"] / 2)
    df["BP_Error"] = abs(df["Systolic"] - df["Expected_Systolic"]) > 10
    df["Calculated_IMC"] = df["Peso (kg)"] / (df["Altura (cm)"] / 100) ** 2
    df["BMI_Consistency_Error"] = abs(df["IMC"] - df["Calculated_IMC"]) > 1

    # Add BMI category and age group
    df["BMI_Category"] = df["IMC"].apply(calculate_bmi_category)
    df["Age_Group"] = df["Edad"].apply(get_age_group)

    # Collect errors
    errors = []
    if df["Weight_Error"].any():
        errors.append(
            f"Unrealistic weights (<20kg or >150kg): {df['Weight_Error'].sum()} rows"
        )
    if df["BMI_Error"].any():
        errors.append(f"Unrealistic BMI (<10 or >50): {df['BMI_Error'].sum()} rows")
    if df["Age_Error"].any():
        errors.append(f"Unrealistic ages (<0 or >120): {df['Age_Error'].sum()} rows")
    if df["BP_Error"].any():
        errors.append(
            f"Blood pressure deviating from formula: {df['BP_Error'].sum()} rows"
        )
    if df["Systolic"].isna().any():
        errors.append(
            f"Invalid blood pressure format: {df['Systolic'].isna().sum()} rows"
        )
    duplicated_ids = df[df["ID_Paciente"].duplicated(keep=False)][
        "ID_Paciente"
    ].unique()
    if len(duplicated_ids) > 0:
        errors.append(
            f"Duplicate patient IDs found: {list(duplicated_ids)} (total: {df['ID_Paciente'].duplicated().sum()} rows)"
        )
    df["Fecha Consulta"] = pd.to_datetime(
        df["Fecha Consulta"], format="%d/%m/%Y", errors="coerce"
    )
    if df["Fecha Consulta"].isna().any():
        errors.append(f"Invalid date formats: {df['Fecha Consulta'].isna().sum()} rows")
    if (df["Fecha Consulta"] > pd.Timestamp.now()).any():
        errors.append(
            f"Future dates detected: {(df['Fecha Consulta'] > pd.Timestamp.now()).sum()} rows"
        )
    if df["BMI_Consistency_Error"].any():
        errors.append(
            f"Inconsistent BMI values: {df['BMI_Consistency_Error'].sum()} rows"
        )

    # Filter out invalid rows
    df = df[
        (df["Edad"].between(0, 120, inclusive="both"))
        & (df["Peso (kg)"].between(10, 200, inclusive="both"))
        & (df["Altura (cm)"].between(50, 250, inclusive="both"))
        & (df["IMC"].between(5, 60, inclusive="both"))
        ]

    return df, errors


def plot_height_age(df, figsize=(12, 6)):
    """Plot height vs. age by gender with averages and linear regression."""
    # Sample to reduce memory usage
    df = df.sample(n=min(10000, len(df)), random_state=42)

    fig, ax = plt.subplots(figsize=figsize)

    for gender, color in [("M", "blue"), ("F", "red")]:
        gender_df = df[df["Género"] == gender]

        # Scatter plot of individual heights
        ax.scatter(
            gender_df["Edad"],
            gender_df["Altura (cm)"],
            alpha=0.2,
            color=color,
            label=f"{gender} (datos)",
        )

        # Average heights per age
        avg_heights = gender_df.groupby("Edad")["Altura (cm)"].mean()
        ax.plot(
            avg_heights.index,
            avg_heights.values,
            color=color,
            linestyle="-",
            linewidth=3,
            label=f"{gender} (promedio por edad)",
        )

        # Linear regression
        if len(gender_df) > 1:
            coef = np.polyfit(gender_df["Edad"], gender_df["Altura (cm)"], 1)
            poly_fn = np.poly1d(coef)
            x_vals = np.linspace(df["Edad"].min(), df["Edad"].max(), 100)
            ax.plot(
                x_vals,
                poly_fn(x_vals),
                color=color,
                linestyle="--",
                linewidth=2,
                label=f"{gender} (regresión lineal)",
            )

            m, b = coef
            ax.text(
                df["Edad"].max(),
                poly_fn(df["Edad"].max()),
                f"{gender} reg: y = {m:.3f}x + {b:.2f}",
                color=color,
                va="center",
            )

    ax.set_xlabel("Edad (años)", fontsize=12)
    ax.set_ylabel("Altura (cm)", fontsize=12)
    ax.set_title("Altura vs Edad: Promedios por Edad y Regresión Lineal", fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(np.arange(15, df["Edad"].max() + 1, 5))
    plt.tight_layout()
    plt.savefig("height_age.png", dpi=300)
    plt.close()


def plot_symptoms_by_age(df, figsize=(12, 6)):
    """Plot frequency of symptoms by age group."""
    # Accumulate counts across chunks
    age_bins = [10, 18, 30, 45, 60, 85]
    df["age_group"] = pd.cut(
        df["Edad"],
        bins=age_bins,
        labels=["<18", "18-29", "30-44", "45-59", "60+"],
        include_lowest=True,
    )

    # Instead of exploding, count symptoms per group directly
    symptom_counts = {}
    for _, row in df.iterrows():
        age_group = row["age_group"]
        symptoms = row["Síntomas"]
        if pd.isna(age_group):
            continue
        for symptom in symptoms:
            key = (age_group, symptom)
            symptom_counts[key] = symptom_counts.get(key, 0) + 1

    # Convert to DataFrame
    symptom_df = pd.DataFrame.from_dict(
        symptom_counts, orient="index", columns=["count"]
    ).reset_index()
    symptom_df[["age_group", "Síntomas"]] = pd.DataFrame(
        symptom_df["index"].tolist(), index=symptom_df.index
    )
    symptom_counts = symptom_df.pivot(
        index="age_group", columns="Síntomas", values="count"
    ).fillna(0)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    bottom = np.zeros(len(symptom_counts))
    colors = plt.cm.tab20(np.linspace(0, 1, len(symptom_counts.columns)))

    for i, symptom in enumerate(symptom_counts.columns):
        ax.bar(
            symptom_counts.index.astype(str),
            symptom_counts[symptom],
            bottom=bottom,
            label=symptom,
            color=colors[i],
        )
        bottom += symptom_counts[symptom]

    ax.set_title("Frecuencia de Síntomas por Grupo de Edad")
    ax.set_ylabel("Frecuencia")
    ax.set_xlabel("Grupo de Edad")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Síntomas")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("symptoms_by_age.png", dpi=300)
    plt.close()


def plot_diagnoses_by_bmi(df, figsize=(12, 6)):
    """Plot diagnoses by BMI category."""
    # Sample to reduce memory usage
    df = df.sample(n=min(10000, len(df)), random_state=42)

    fig, ax = plt.subplots(figsize=figsize)

    # Extract diagnosis description
    df["diagnosis_desc"] = df["Diagnóstico (CIE-10)"].str.split(" - ").str[1]
    diagnosis_counts = (
        df.groupby(["BMI_Category", "diagnosis_desc"], observed=True)
        .size()
        .unstack()
        .fillna(0)
    )
    bottom = np.zeros(len(diagnosis_counts))
    colors = plt.cm.tab20(np.linspace(0, 1, len(diagnosis_counts.columns)))

    for i, diagnosis in enumerate(diagnosis_counts.columns):
        ax.bar(
            diagnosis_counts.index.astype(str),
            diagnosis_counts[diagnosis],
            bottom=bottom,
            label=diagnosis,
            color=colors[i],
        )
        bottom += diagnosis_counts[diagnosis]

    ax.set_title("Diagnósticos por Categoría de BMI")
    ax.set_ylabel("Frecuencia")
    ax.set_xlabel("Categoría de BMI")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Diagnósticos")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("diagnoses_by_bmi.png", dpi=300)
    plt.close()


def plot_age_distribution(df, figsize=(10, 6)):
    # Sample to reduce memory usage
    df = df.sample(n=min(10000, len(df)), random_state=42)

    plt.figure(figsize=figsize)
    sns.histplot(df["Edad"], kde=True, stat="density", bins=30)
    mu, sigma = df["Edad"].mean(), df["Edad"].std()
    x = np.linspace(df["Edad"].min(), df["Edad"].max(), 100)
    plt.plot(x, norm.pdf(x, mu, sigma), "r-", lw=2, label="Distribución Normal")
    plt.title("Distribución de Edades con Ajuste Normal")
    plt.xlabel("Edad (años)")
    plt.ylabel("Densidad")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("age_distribution.png", dpi=300)
    plt.close()


def plot_height_distribution(df, figsize=(10, 6)):
    # Sample to reduce memory usage
    df = df.sample(n=min(10000, len(df)), random_state=42)

    plt.figure(figsize=figsize)
    for gender, color in [("M", "blue"), ("F", "red")]:
        data = df[df["Género"] == gender]["Altura (cm)"]
        sns.histplot(
            data,
            kde=True,
            stat="density",
            bins=20,
            label=gender,
            color=color,
            alpha=0.5,
        )
        mu, sigma = data.mean(), data.std()
        x = np.linspace(data.min(), data.max(), 100)
        plt.plot(x, norm.pdf(x, mu, sigma), color=color, lw=2, label=f"{gender} Normal")
    plt.title("Distribución de Altura por Género con Ajuste Normal")
    plt.xlabel("Altura (cm)")
    plt.ylabel("Densidad")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("height_distribution.png", dpi=300)
    plt.close()


def plot_weight_vs_age(df, figsize=(12, 6)):
    # Sample to reduce memory usage
    df = df.sample(n=min(10000, len(df)), random_state=42)

    plt.figure(figsize=figsize)
    for gender, color in [("M", "blue"), ("F", "red")]:
        data = df[df["Género"] == gender]
        plt.scatter(
            data["Edad"], data["Peso (kg)"], label=gender, color=color, alpha=0.5
        )
        coef = np.polyfit(data["Edad"], data["Peso (kg)"], 1)
        plt.plot(
            data["Edad"], np.poly1d(coef)(data["Edad"]), color=color, linestyle="--"
        )
    plt.title("Peso vs. Edad por Género con Regresión Lineal")
    plt.xlabel("Edad (años)")
    plt.ylabel("Peso (kg)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("weight_vs_age.png", dpi=300)
    plt.close()


def plot_symptoms_count(df, figsize=(14, 8)):
    """Plot age vs. BMI with number of symptoms as size and color."""
    # Sample to reduce memory usage
    sample_df = (
        df.sample(n=min(1000, len(df)), random_state=42) if len(df) > 1000 else df
    )

    fig, ax = plt.subplots(figsize=figsize)

    # Calculate number of symptoms
    sample_df["num_symptoms"] = sample_df["Síntomas"].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )

    cmap = plt.cm.get_cmap("plasma")
    norm = plt.Normalize(
        sample_df["num_symptoms"].min(), sample_df["num_symptoms"].max()
    )

    for num in sorted(sample_df["num_symptoms"].unique()):
        subset = sample_df[sample_df["num_symptoms"] == num]
        if not subset.empty:
            size = 50 + num * 30
            ax.scatter(
                subset["Edad"],
                subset["IMC"],
                c=cmap(norm(num)),
                s=size,
                alpha=0.7,
                edgecolors="w",
                linewidth=0.5,
                label=f"{num} síntoma(s)" if num == 1 else f"{num} síntomas",
            )

    ax.set_title("Relación entre Edad, BMI y Número de Síntomas", fontsize=16, pad=20)
    ax.set_xlabel("Edad (años)", fontsize=12)
    ax.set_ylabel("Índice de Masa Corporal (BMI)", fontsize=12)

    ax.axhline(y=18.5, color="yellow", linestyle="--", alpha=0.5, linewidth=1)
    ax.axhline(y=25, color="green", linestyle="--", alpha=0.5, linewidth=1)
    ax.axhline(y=30, color="orange", linestyle="--", alpha=0.5, linewidth=1)

    legend = ax.legend(
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        title="Número de Síntomas",
        frameon=True,
        framealpha=0.9,
    )
    legend.get_title().set_fontsize(11)

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Número de Síntomas", rotation=270, labelpad=15)

    ax.set_xticks(np.arange(sample_df["Edad"].min(), sample_df["Edad"].max() + 1, 5))
    ax.set_yticks(np.arange(5, 61, 5))
    ax.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig("symptoms_count.png", dpi=300)
    plt.close()


def plot_chronic_diseases_by_locality(df, figsize=(12, 6)):
    """Plot chronic diseases by locality."""
    # Accumulate counts across chunks
    chronic_counts = {}
    for _, row in df.iterrows():
        locality = row["Localidad"]
        diseases = row["Enfermedades Crónicas"]
        if pd.isna(locality):
            continue
        for disease in diseases:
            key = (locality, disease)
            chronic_counts[key] = chronic_counts.get(key, 0) + 1

    # Convert to DataFrame
    chronic_df = pd.DataFrame.from_dict(
        chronic_counts, orient="index", columns=["count"]
    ).reset_index()
    chronic_df[["Localidad", "Enfermedades Crónicas"]] = pd.DataFrame(
        chronic_df["index"].tolist(), index=chronic_df.index
    )
    counts = chronic_df.pivot(
        index="Localidad", columns="Enfermedades Crónicas", values="count"
    ).fillna(0)

    # Plot
    plt.figure(figsize=figsize)
    counts.plot(kind="bar", stacked=True, cmap="tab20")
    plt.title("Enfermedades Crónicas por Localidad")
    plt.xlabel("Localidad")
    plt.ylabel("Frecuencia")
    plt.legend(title="Enfermedades", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("chronic_diseases_by_locality.png", dpi=300)
    plt.close()


def plot_consultations_by_month(df, figsize=(12, 6)):
    """Plot consultations by month."""
    # Accumulate counts across chunks
    df["Month"] = df["Fecha Consulta"].dt.to_period("M")
    counts = df.groupby("Month").size()

    # Plot
    plt.figure(figsize=figsize)
    counts.plot(kind="line", marker="o")
    plt.title("Consultas por Mes")
    plt.xlabel("Mes")
    plt.ylabel("Número de Consultas")
    plt.grid(alpha=0.3)
    plt.savefig("consultations_by_month.png", dpi=300)
    plt.close()


def plot_diagnoses_cie10(df, figsize=(12, 6)):
    """Plot a bar chart of CIE-10 diagnoses and their frequency."""
    # Accumulate counts across chunks
    diagnosis_counts = df["Diagnóstico (CIE-10)"].value_counts()

    plt.figure(figsize=figsize)
    diagnosis_counts.plot(kind="bar", color="skyblue")
    plt.title("Frecuencia de Diagnósticos CIE-10")
    plt.xlabel("Diagnóstico (CIE-10)")
    plt.ylabel("Número de Apariciones")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("diagnoses_cie10.png", dpi=300)
    plt.close()


def plot_hospitals_frequency(df, figsize=(12, 6)):
    """Plot a bar chart of hospitals and their frequency."""
    # Accumulate counts across chunks
    hospital_counts = df["Hospital"].value_counts()

    plt.figure(figsize=figsize)
    hospital_counts.plot(kind="bar", color="lightgreen")
    plt.title("Frecuencia de Consultas por Hospital")
    plt.xlabel("Hospital")
    plt.ylabel("Número de Consultas")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("hospitals_frequency.png", dpi=300)
    plt.close()


def plot_socioeconomic_distribution(df, figsize=(8, 8)):
    """Plot a pie chart of socioeconomic level distribution."""
    # Accumulate counts across chunks
    socioeconomic_counts = df["Nivel Socioeconómico"].value_counts()

    plt.figure(figsize=figsize)
    labels = [
        f"{index} ({count / sum(socioeconomic_counts) * 100:.1f}%)"
        for index, count in socioeconomic_counts.items()
    ]
    plt.pie(
        socioeconomic_counts,
        labels=labels,
        colors=["#ff9999", "#66b3ff", "#99ff99"],
        startangle=90,
    )
    plt.title("Distribución de Niveles Socioeconómicos")
    plt.axis("equal")
    plt.savefig("socioeconomic_distribution.png", dpi=300)
    plt.close()


def plot_gender_distribution(df, figsize=(8, 8)):
    """Plot a pie chart of gender distribution."""
    # Accumulate counts across chunks
    gender_counts = df["Género"].value_counts()

    plt.figure(figsize=figsize)
    labels = [
        f"{index} ({count / sum(gender_counts) * 100:.1f}%)"
        for index, count in gender_counts.items()
    ]
    plt.pie(gender_counts, labels=labels, colors=["#1f77b4", "#ff7f0e"], startangle=90)
    plt.title("Distribución por Género")
    plt.axis("equal")
    plt.savefig("gender_distribution.png", dpi=300)
    plt.close()


def main(file_path="data014_medium.csv"):
    """Run analysis and generate visualizations."""
    try:
        # Initialize accumulators for visualizations that need full data
        chunksize = 100000  # Adjust based on your system's memory
        total_records = 0
        errors_list = []
        all_dfs = []

        # Min/Max accumulators
        min_age = float("inf")
        max_age = float("-inf")
        min_weight = float("inf")
        max_weight = float("-inf")
        min_height = float("inf")
        max_height = float("-inf")
        min_date = None
        max_date = None

        print("Processing data in chunks...")

        # Process the CSV in chunks
        for chunk in pd.read_csv(file_path, encoding="utf-8", chunksize=chunksize, dtype=DTYPES):
            # Clean and validate each chunk
            df_clean, errors = clean_and_validate_data(chunk)
            total_records += len(df_clean)
            errors_list.extend(errors)

            if not df_clean.empty:
                all_dfs.append(df_clean)

            # Update min/max values
            if not df_clean["Edad"].isna().all():
                min_age = min(min_age, df_clean["Edad"].min())
                max_age = max(max_age, df_clean["Edad"].max())
            if not df_clean["Peso (kg)"].isna().all():
                min_weight = min(min_weight, df_clean["Peso (kg)"].min())
                max_weight = max(max_weight, df_clean["Peso (kg)"].max())
            if not df_clean["Altura (cm)"].isna().all():
                min_height = min(min_height, df_clean["Altura (cm)"].min())
                max_height = max(max_height, df_clean["Altura (cm)"].max())
            if not df_clean["Fecha Consulta"].isna().all():
                chunk_min_date = df_clean["Fecha Consulta"].min()
                chunk_max_date = df_clean["Fecha Consulta"].max()
                if min_date is None or (chunk_min_date is not pd.NaT and chunk_min_date < min_date):
                    min_date = chunk_min_date
                if max_date is None or (chunk_max_date is not pd.NaT and chunk_max_date > max_date):
                    max_date = chunk_max_date




        if not all_dfs:
            print("No valid data after cleaning. Check errors:")
            for error in errors_list:
                print(error)
            return None, errors_list, {}

        # Concatenate all chunks for visualizations
        print("Concatenating cleaned chunks...")
        df_clean = pd.concat(all_dfs, ignore_index=True)

        # Generate visualizations
        print("Generating visualizations...")
        plot_height_age(df_clean)
        plot_symptoms_by_age(df_clean)
        plot_diagnoses_by_bmi(df_clean)
        plot_symptoms_count(df_clean)
        plot_age_distribution(df_clean)
        plot_height_distribution(df_clean)
        plot_weight_vs_age(df_clean)
        plot_chronic_diseases_by_locality(df_clean)
        plot_consultations_by_month(df_clean)
        plot_diagnoses_cie10(df_clean)
        plot_hospitals_frequency(df_clean)
        plot_socioeconomic_distribution(df_clean)
        plot_gender_distribution(df_clean)

        # Print results
        print("=== Data Analysis Results ===")
        print(f"Total Records: {total_records}")
        print("\nMin/Max Values:")
        print(f"Edad mínima: {min_age}")
        print(f"Edad máxima: {max_age}")
        print(f"Peso mínimo: {min_weight} kg")
        print(f"Peso máximo: {max_weight} kg")
        print(f"Altura mínima: {min_height} cm")
        print(f"Altura máxima: {max_height} cm")
        print(f"Fecha de consulta mínima: {min_date}")
        print(f"Fecha de consulta máxima: {max_date}")
        print("\nError Detection:")
        for error in errors_list:
            print(error)

        print("\nVisualizations generated successfully. Check the following files:")
        print("- height_age.png")
        print("- symptoms_by_age.png")
        print("- diagnoses_by_bmi.png")
        print("- symptoms_count.png")
        print("- age_distribution.png")
        print("- height_distribution.png")
        print("- weight_vs_age.png")
        print("- chronic_diseases_by_locality.png")
        print("- consultations_by_month.png")
        print("- diagnoses_cie10.png")
        print("- hospitals_frequency.png")
        print("- socioeconomic_distribution.png")
        print("- gender_distribution.png")

        return df_clean, errors_list, {}

    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return None, [str(e)], {}


if __name__ == "__main__":
    df, errors, results = main()