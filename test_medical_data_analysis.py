import unittest
import pandas as pd
import numpy as np
import os
from medical_data_analysis import (
    parse_blood_pressure,
    calculate_bmi_category,
    get_age_group,
    clean_and_validate_data,
    plot_height_age,
    plot_symptoms_by_age,
    plot_diagnoses_by_bmi,
    plot_symptoms_count,
    plot_age_distribution,
    plot_height_distribution,
    plot_weight_vs_age,
    plot_chronic_diseases_by_locality,
    plot_consultations_by_month,
    plot_correlation_matrix,
    plot_diagnoses_cie10,
    plot_hospitals_frequency,
    plot_socioeconomic_distribution,
    plot_gender_distribution,
)


class TestMedicalDataAnalysis(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.sample_data = pd.DataFrame(
            {
                "ID_Paciente": ["a1", "a1", "a3"],  # Duplicate ID
                "Género": ["M", "F", "M"],
                "Edad": [15, 30, 65],
                "Peso (kg)": [60.0, 55.0, 80.0],
                "Altura (cm)": [170, 160, 175],
                "IMC": [20.8, 21.5, 26.1],
                "Presión Arterial": ["120/80 mmHg", "110/70 mmHg", "130/85 mmHg"],
                "Síntomas": [
                    "Tos persistente",
                    "Fiebre, Dolor de cabeza",
                    "Fatiga",
                ],  # Changed to comma-separated strings
                "Diagnóstico (CIE-10)": [
                    "J20.9 - Bronquitis aguda",
                    "A15.0 - Gripe viral",
                    "E11 - Diabetes tipo 2",
                ],
                "Enfermedades Crónicas": [
                    "Ninguna",
                    "Ninguna",
                    "Hipertensión",
                ],  # Changed to comma-separated strings
                "Fecha Consulta": ["25/04/2023", "25/04/2023", "25/04/2023"],
                "Hospital": [
                    "Hospital San Ignacio",
                    "Hospital San Ignacio",
                    "Hospital San Ignacio",
                ],
                "Localidad": [
                    "Santa Fe",
                    "Kennedy",
                    "Santa Fe",
                ],  # Inconsistent locality
                "Nivel Socioeconómico": ["Medio", "Bajo", "Alto"],
                "Seguro Médico": [
                    "EPS Sura",
                    "EPS Sura",
                    "SISBEN",
                ],  # Inconsistent insurance
            }
        )

    def test_parse_blood_pressure(self):
        systolic, diastolic = parse_blood_pressure("120/80 mmHg")
        self.assertEqual(systolic, 120)
        self.assertEqual(diastolic, 80)
        systolic, diastolic = parse_blood_pressure("invalid")
        self.assertTrue(np.isnan(systolic))
        self.assertTrue(np.isnan(diastolic))

    def test_calculate_bmi_category(self):
        self.assertEqual(calculate_bmi_category(18.0), "Underweight")
        self.assertEqual(calculate_bmi_category(22.0), "Normal")
        self.assertEqual(calculate_bmi_category(27.0), "Overweight")
        self.assertEqual(calculate_bmi_category(31.0), "Obese")
        self.assertEqual(calculate_bmi_category(np.nan), "Unknown")

    def test_get_age_group(self):
        self.assertEqual(get_age_group(15), "<18")
        self.assertEqual(get_age_group(30), "18-60")
        self.assertEqual(get_age_group(65), ">60")
        self.assertEqual(get_age_group(np.nan), "Unknown")

    def test_clean_and_validate_data(self):
        df, errors = clean_and_validate_data(self.sample_data.copy())
        self.assertEqual(len(df), 3)
        self.assertTrue(all(df["Systolic"].notna()))
        self.assertTrue(all(df["Diastolic"].notna()))
        self.assertTrue(all(df["Edad"] >= 0))
        self.assertTrue(all(df["IMC"] >= 0))
        self.assertIn("BMI_Category", df.columns)
        self.assertIn("Age_Group", df.columns)
        self.assertIn("Weight_Error", df.columns)
        self.assertFalse(df["Weight_Error"].any())
        self.assertFalse(df["BMI_Error"].any())
        self.assertFalse(df["Age_Error"].any())
        # Check for duplicate IDs
        self.assertTrue(
            any("Duplicate patient IDs found: ['a1']" in error for error in errors)
        )

    def test_plot_height_age(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_height_age(df)
        self.assertTrue(os.path.exists("height_age.png"))
        os.remove("height_age.png")

    def test_plot_symptoms_by_age(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_symptoms_by_age(df)
        self.assertTrue(os.path.exists("symptoms_by_age.png"))
        os.remove("symptoms_by_age.png")

    def test_plot_diagnoses_by_bmi(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_diagnoses_by_bmi(df)
        self.assertTrue(os.path.exists("diagnoses_by_bmi.png"))
        os.remove("diagnoses_by_bmi.png")

    def test_plot_symptoms_count(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_symptoms_count(df)
        self.assertTrue(os.path.exists("symptoms_count.png"))
        os.remove("symptoms_count.png")

    def test_plot_age_distribution(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_age_distribution(df)
        self.assertTrue(os.path.exists("age_distribution.png"))
        os.remove("age_distribution.png")

    def test_plot_height_distribution(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_height_distribution(df)
        self.assertTrue(os.path.exists("height_distribution.png"))
        os.remove("height_distribution.png")

    def test_plot_weight_vs_age(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_weight_vs_age(df)
        self.assertTrue(os.path.exists("weight_vs_age.png"))
        os.remove("weight_vs_age.png")

    def test_plot_chronic_diseases_by_locality(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_chronic_diseases_by_locality(df)
        self.assertTrue(os.path.exists("chronic_diseases_by_locality.png"))
        os.remove("chronic_diseases_by_locality.png")

    def test_plot_consultations_by_month(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_consultations_by_month(df)
        self.assertTrue(os.path.exists("consultations_by_month.png"))
        os.remove("consultations_by_month.png")

    def test_plot_correlation_matrix(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_correlation_matrix(df)
        self.assertTrue(os.path.exists("correlation_matrix.png"))
        os.remove("correlation_matrix.png")

    def test_plot_diagnoses_cie10(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_diagnoses_cie10(df)
        self.assertTrue(os.path.exists("diagnoses_cie10.png"))
        os.remove("diagnoses_cie10.png")

    def test_plot_hospitals_frequency(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_hospitals_frequency(df)
        self.assertTrue(os.path.exists("hospitals_frequency.png"))
        os.remove("hospitals_frequency.png")

    def test_plot_socioeconomic_distribution(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_socioeconomic_distribution(df)
        self.assertTrue(os.path.exists("socioeconomic_distribution.png"))
        os.remove("socioeconomic_distribution.png")

    def test_plot_gender_distribution(self):
        df, _ = clean_and_validate_data(self.sample_data.copy())
        plot_gender_distribution(df)
        self.assertTrue(os.path.exists("gender_distribution.png"))
        os.remove("gender_distribution.png")


if __name__ == "__main__":
    unittest.main()
