import os
import sys
import pandas as pd

# Allow importing the V2 pipeline
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, BASE_DIR)

from verification.v2_full_pipeline import (
    ml_prediction,
    collect_evidence,
    calculate_final_evidence,
    calculate_final_decision
)


# ============================================================
# CONFIGURATION
# ============================================================

TEST_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "external_test.csv"
)


# ============================================================
# TEST ONE ARTICLE
# ============================================================

def test_article(row):

    headline = str(row["title"])
    article = str(row["text"])
    actual_label = int(row["actual_label"])

    # --------------------------------------------------------
    # ML
    # --------------------------------------------------------

    ml_label, ml_confidence = ml_prediction(
        headline,
        article
    )

    # --------------------------------------------------------
    # External Evidence
    # --------------------------------------------------------

    evidence = collect_evidence(
        headline,
        article
    )

    # --------------------------------------------------------
    # Evidence Decision
    # --------------------------------------------------------

    evidence_result = calculate_final_evidence(
        evidence
    )

    # --------------------------------------------------------
    # Final Decision
    # --------------------------------------------------------

    final_assessment, final_confidence = (
        calculate_final_decision(
            ml_label,
            ml_confidence,
            evidence_result
        )
    )

    # --------------------------------------------------------
    # Convert final result to binary label
    #
    # REAL = 1
    # FAKE = 0
    # NEEDS VERIFICATION = None
    # --------------------------------------------------------

    if final_assessment == "REAL":
        final_label = 1

    elif final_assessment == "FAKE":
        final_label = 0

    else:
        final_label = None

    return {
        "title": headline,
        "source": row["source"],
        "actual_label": actual_label,
        "ml_prediction": ml_label,
        "ml_confidence": ml_confidence,
        "evidence_assessment":
            evidence_result["assessment"],
        "evidence_score":
            evidence_result["score"],
        "evidence_level":
            evidence_result["level"],
        "final_assessment":
            final_assessment,
        "final_confidence":
            final_confidence,
        "final_label":
            final_label,
        "evidence_count":
            len(evidence),
        "trusted_sources":
            sum(
                e["trusted"]
                for e in evidence
            ),
        "strong_supporting":
            evidence_result[
                "strong_supporting"
            ],
        "strong_contradicting":
            evidence_result[
                "strong_contradicting"
            ],
    }


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print("=" * 70)
    print("V2 FULL PIPELINE — EXTERNAL VALIDATION")
    print("=" * 70)

    print(
        f"\nLoading dataset:\n{TEST_FILE}\n"
    )

    df = pd.read_csv(TEST_FILE)

    print(
        f"Articles to test: {len(df)}"
    )

    results = []

    # ========================================================
    # PROCESS EACH ARTICLE
    # ========================================================

    for index, row in df.iterrows():

        print("\n")
        print("-" * 70)
        print(
            f"ARTICLE {index + 1}/{len(df)}"
        )
        print("-" * 70)

        print(
            f"Title: {row['title']}"
        )

        print(
            f"Actual label: "
            f"{'REAL' if int(row['actual_label']) == 1 else 'FAKE'}"
        )

        try:

            result = test_article(row)

            results.append(result)

            print(
                f"ML: "
                f"{result['ml_prediction']} "
                f"({result['ml_confidence'] * 100:.2f}%)"
            )

            print(
                f"Evidence: "
                f"{result['evidence_assessment']} "
                f"({result['evidence_score'] * 100:.2f}%)"
            )

            print(
                f"Final: "
                f"{result['final_assessment']} "
                f"({result['final_confidence'] * 100:.2f}%)"
            )

            print(
                f"Evidence sources: "
                f"{result['evidence_count']}"
            )

            print(
                f"Trusted sources: "
                f"{result['trusted_sources']}"
            )

        except Exception as e:

            print(
                f"ERROR: {e}"
            )


    # ========================================================
    # RESULTS DATAFRAME
    # ========================================================

    results_df = pd.DataFrame(results)

    if results_df.empty:

        print(
            "\nNo results generated."
        )

        return


    # ========================================================
    # ML PERFORMANCE
    # ========================================================

    ml_correct = (
        (
            results_df["ml_prediction"]
            == results_df["actual_label"]
            .map({
                0: "FAKE",
                1: "REAL"
            })
        )
        .sum()
    )

    ml_accuracy = (
        ml_correct
        / len(results_df)
    )


    # ========================================================
    # FINAL PIPELINE PERFORMANCE
    # ========================================================

    evaluated = results_df[
        results_df["final_label"].notna()
    ]

    final_correct = (
        (
            evaluated["final_label"]
            == evaluated["actual_label"]
        )
        .sum()
    )

    final_accuracy = (
        final_correct
        / len(evaluated)
        if len(evaluated) > 0
        else 0
    )


    # ========================================================
    # NEEDS VERIFICATION
    # ========================================================

    needs_verification = (
        results_df["final_assessment"]
        == "NEEDS VERIFICATION"
    ).sum()


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n\n")

    print("=" * 70)
    print("V2 FINAL VALIDATION RESULTS")
    print("=" * 70)

    print(
        f"\nTotal articles tested: "
        f"{len(results_df)}"
    )

    print(
        f"\nML accuracy: "
        f"{ml_accuracy * 100:.2f}%"
    )

    print(
        f"Final pipeline accuracy "
        f"(excluding NEEDS VERIFICATION): "
        f"{final_accuracy * 100:.2f}%"
    )

    print(
        f"Needs verification: "
        f"{needs_verification}"
    )

    print("\n")

    # ========================================================
    # ARTICLE-BY-ARTICLE TABLE
    # ========================================================

    display_columns = [
        "title",
        "actual_label",
        "ml_prediction",
        "evidence_assessment",
        "final_assessment",
        "final_confidence",
        "evidence_count",
        "trusted_sources"
    ]

    print(
        results_df[
            display_columns
        ].to_string(index=False)
    )


    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output_file = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "v2_full_pipeline_results.csv"
    )

    results_df.to_csv(
        output_file,
        index=False
    )

    print(
        f"\n\nResults saved to:"
    )

    print(output_file)

    print(
        "\nV2 FULL PIPELINE VALIDATION COMPLETE."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()