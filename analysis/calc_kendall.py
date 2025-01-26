import argparse

import pandas as pd
from scipy.stats import kendalltau


def parse_args():
    parser = argparse.ArgumentParser(description="Load a dataframe from a file.")
    parser.add_argument("-f", "--filepath", type=str, required=True, help="Path to the file to load.")
    parser.add_argument("-d", "--domain", type=str, required=True, help="Domain parameter for processing.")
    return parser.parse_args()


def load_file(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unknown file extension to load dataframe from")


def extract_optimal_solutions(df):
    df = df[(df['weight'] == 1) & (df['quality'] == 1)]

    unique_solutions = df.groupby('id')['solution'].nunique()
    if any(unique_solutions > 1):
        raise ValueError("Some IDs have multiple solutions.")

    df = df.drop_duplicates(subset=['id'])

    ids = df['id'].sort_values()
    if not all(ids == range(len(ids))):
        raise ValueError("IDs are not consecutive from 0 to n.")

    ordered_solutions = df.sort_values('id')['solution'].tolist()

    return ordered_solutions


def main():
    args = parse_args()
    df = load_file(args.filepath)
    optimal_costs = extract_optimal_solutions(df)
    for heuristic_optimal in df["heuristic-optimal"].unique():
        for heuristic_greedy in df["heuristic-greedy"].unique():
            for epsilon in df["epsilon"].unique():
                subset = df[
                    (df["heuristic-optimal"] == heuristic_optimal) & (df["heuristic-greedy"] == heuristic_greedy) & (
                            df["epsilon"] == epsilon)]
                if subset.empty:
                    continue
                subset = subset.sort_values(by='id', ascending=True)
                tau, _ = kendalltau(optimal_costs, subset["init-h"])
                hdiff = 1-sum([h/o for o, h in zip(optimal_costs, subset["init-h"])])/len(optimal_costs)
                print(
                    f"Heuristic Optimal: {heuristic_optimal}, Heuristic Greedy: {heuristic_greedy}, Epsilon: {epsilon}, Kendall's Tau: {tau}, H-Diff: {hdiff}")


if __name__ == '__main__':
    main()
