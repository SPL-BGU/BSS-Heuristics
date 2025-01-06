import argparse
from pathlib import Path
from typing import Union

import pandas as pd
from pandas import DataFrame


def parse_file(file_path: Path) -> DataFrame:
    current_dict = {}
    dicts = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('[D]') or line.startswith('[I]') or line.startswith('[R]'):
                current_dict.update(dict(item.split(": ") for item in line[3:].strip().split("; ")))
                if line.startswith('[R]'):
                    dicts.append(current_dict.copy())
    return DataFrame(dicts)


def parse_dir(dir_path: Union[Path, str]) -> DataFrame:
    dir_path = Path(dir_path)
    dfs = [parse_file(file_path) for file_path in dir_path.rglob('*') if file_path.suffix in ['.out', '.txt', '.log']]
    full_df = pd.concat(dfs, ignore_index=True)
    full_df['time'] = full_df['time'].apply(lambda x: x[:-1] if x.endswith('s') else x)  # Remove unit from time
    full_df.drop(columns=['instance'], inplace=True)
    full_df['id'] = full_df['id'].astype(int)
    full_df['expanded'] = full_df['expanded'].astype(int)
    full_df['solution'] = full_df['solution'].astype(float)
    full_df['weight'] = full_df['weight'].astype(float)
    full_df['epsilon'] = full_df['epsilon'].astype(float)
    full_df['time'] = full_df['time'].astype(float)

    optimal_solutions = get_optimal_solutions(full_df)
    full_df = add_solution_quality(full_df, optimal_solutions)
    return full_df


def add_solution_quality(df, solutions):
    df['quality'] = df.apply(lambda row: row['solution'] / solutions[row['id']], axis=1)
    return df


def verify_quality(df):
    if not ((df['quality'] >= 1) & (df['quality'] <= df['weight'])).all():
        raise ValueError("Some rows have 'quality' not between 1 and 'weight'.")


def parse_args():
    parser = argparse.ArgumentParser(description="Process log directory and output file.")
    parser.add_argument('-l', '--log-dir', type=str, required=True, help="Path to the log directory")
    parser.add_argument('-o', '--output', type=str, required=True, help="Path to the output file")
    return parser.parse_args()


def get_optimal_solutions(df):
    filtered_df = df[df['weight'] == 1]
    grouped = filtered_df.groupby('id')['solution']
    for id_value, solutions in grouped:
        if len(solutions.unique()) > 1:
            raise ValueError(f"Inconsistent solutions found for id: {id_value}")

    id_to_solution = grouped.first().to_dict()
    return id_to_solution


def main():
    args = parse_args()
    df = parse_dir(args.log_dir)
    verify_quality(df)
    if args.output.endswith('.xlsx'):
        df.to_excel(args.output, index=False)
    else:
        df.to_csv(args.output, index=False)


if __name__ == '__main__':
    main()
