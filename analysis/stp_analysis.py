from decimal import Decimal, ROUND_HALF_UP
from os import PathLike
from pathlib import Path

import pandas as pd
from pandas import DataFrame
from scipy.stats import kendalltau


def round_half_up(value, decimals):
    d = Decimal(value)
    return d.quantize(Decimal('1e-{0}'.format(decimals)), rounding=ROUND_HALF_UP)


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


def parse_dir(dir_path: str | PathLike[str]):
    dir_path = Path(dir_path)
    dfs = [parse_file(file_path) for file_path in dir_path.rglob('*') if file_path.suffix in ['.out', '.txt', '.log']]
    return (generate_results_df([df for df in dfs if 'init-ho' not in df.columns]),
            generate_init_heuristic_df([df for df in dfs if 'init-ho' in df.columns]))


def generate_init_heuristic_df(dfs_list):
    df = pd.concat(dfs_list, ignore_index=True)
    df.drop(columns=['instance', 'weight', 'epsilon', 'alg'], inplace=True)
    df['id'] = df['id'].astype(float)
    df['init-hg'] = df['init-hg'].astype(float)
    df['init-ho'] = df['init-ho'].astype(float)
    return df


def generate_results_df(dfs_list):
    df = pd.concat(dfs_list, ignore_index=True)
    df['time'] = df['time'].apply(lambda x: x[:-1] if str(x).endswith('s') else x)  # Remove unit from time
    df.drop(columns=['instance'], inplace=True)
    df['id'] = df['id'].astype(int)
    df['expanded'] = df['expanded'].astype(int)
    df['solution'] = df['solution'].astype(float)
    df['weight'] = df['weight'].astype(float)
    df['epsilon'] = df['epsilon'].astype(float)
    df['time'] = df['time'].astype(float)
    return df


def get_optimal_solutions(df):
    filtered_df = df[(df['weight'] == 1) & (df['alg'] != 'gbfs')]
    grouped = filtered_df.groupby('id')['solution']
    for id_value, solutions in grouped:
        if len(solutions.unique()) > 1:
            raise ValueError(f"Inconsistent solutions found for id: {id_value}")

    id_to_solution = grouped.first().to_dict()
    return id_to_solution


def add_solution_quality(df, solutions):
    df['quality'] = df.apply(lambda row: row['solution'] / solutions[row['id']], axis=1)
    verify_quality(df)
    return df


def verify_quality(df):
    if not (((df['quality'] >= 1) & (df['quality'] <= df['weight'])) | (df['alg'] == 'gbfs')).all():
        raise ValueError("Some rows have 'quality' not between 1 and 'weight'.")


def verify_heuristics(df, solutions):
    if not ((df['init-ho'] <= df['id'].map(solutions)) & (df['init-hg'] <= df['id'].map(solutions))).all():
        raise ValueError("Some heuristics are not admissible.")


def gen_wa_table_latex(result_df, h_df, solution_list):
    gbfs_df = result_df[(result_df['alg'] == 'gbfs')]
    gbfs_pivot = gbfs_df.pivot_table(values=['expanded', 'quality'],
                                     index=['heuristic-optimal', 'heuristic-greedy', 'epsilon'],
                                     aggfunc='mean')
    result_df = result_df[(result_df['alg'] == 'wa')]
    pivot = result_df.pivot_table(
        index=['heuristic-optimal', 'heuristic-greedy', 'epsilon'],
        columns='weight',
        values=['expanded', 'quality', 'id'],
        aggfunc={'expanded': 'mean', 'quality': 'mean', 'id': 'count'}
    )
    pivot = pivot.sort_index(level='epsilon', ascending=False).reset_index()
    pivot = pivot.sort_values(by=['heuristic-optimal', 'epsilon'], ascending=[True, False])
    latex_str = r"\begin{tabular}{ccccc" + ('r' * 2 * len(WEIGHTS)) + "rr}\n"
    latex_str += '\\toprule\nOptimal & Greedy & Epsilon & $h/C^*$ & GDRC '
    for weight in WEIGHTS:
        latex_str += f' & {weight}-e & {weight}-q'
    latex_str += ' & GBFS-e & GBFS-q \\\\\n\\midrule\n'
    # Iterate over each row and print column names
    for _, row in pivot.iterrows():
        ho = row[('heuristic-optimal', '')]
        hg = row[('heuristic-greedy', '')]
        epsilon = row[('epsilon', '')]
        subset_df = h_df[(h_df["heuristic-optimal"] == ho) & (h_df["heuristic-greedy"] == hg)]
        subset_df = subset_df.sort_values(by='id', ascending=True)
        heuristic_values = epsilon * subset_df['init-ho'] + (1 - epsilon) * subset_df['init-hg']
        tau, _ = kendalltau(solution_list, heuristic_values)

        hdiff = sum([hv / sc for hv, sc in zip(heuristic_values, solution_list)]) / len(heuristic_values)
        latex_str += f'{ho} & {hg} & {round_half_up(epsilon, 2)} & {round_half_up(hdiff, 3)} & {round_half_up(tau, 3)}'
        for weight in WEIGHTS:
            if row[('id', weight)] == 100:
                latex_str += f" & {round_half_up(row[('expanded', weight)], 0):,} & {round_half_up(row[('quality', weight)], 3):,}"
            else:
                latex_str += f" & \multicolumn{{2}}{{c}}{{\#{row[('id', weight)]}}}"
        gbfs_result = gbfs_pivot.loc[(gbfs_pivot.index.get_level_values('epsilon') == epsilon) &
                                     (gbfs_pivot.index.get_level_values('heuristic-optimal') == ho) &
                                     (gbfs_pivot.index.get_level_values('heuristic-greedy') == hg)]
        gbfs_expanded = round_half_up(gbfs_result['expanded'].iloc[0], 0)
        gbfs_quality = round_half_up(gbfs_result['quality'].iloc[0], 3)
        latex_str += f" & {gbfs_expanded:,} & {gbfs_quality}"
        latex_str += ' \\\\\n'
    latex_str += '\\bottomrule\n\\end{tabular}'
    with open('results/latex/stp_wa_table.tex', 'w+') as f:
        f.write(latex_str)


def write_to_excel(result_df, h_df, filename="results/stp.xlsx"):
    with pd.ExcelWriter(filename) as writer:
        result_df.to_excel(writer, sheet_name="results", index=False)
        h_df.to_excel(writer, sheet_name="heuristics", index=False)


def gen_ios_table_latex(result_df, h_df, solution_list):
    result_df = result_df[result_df['alg'] == 'ios']
    pivot = result_df.pivot_table(
        index=['heuristic-optimal', 'heuristic-greedy', 'epsilon'],
        columns='weight',
        values=['expanded', 'quality', 'id'],
        aggfunc={'expanded': 'mean', 'quality': 'mean', 'id': 'count'}
    )
    pivot = pivot.sort_index(level='epsilon', ascending=False).reset_index()
    latex_str = r"\begin{tabular}{ccccc" + ('r' * 2 * len(WEIGHTS[1:])) + "rr}\n"
    latex_str += '\\toprule\n\\multirow{2}{*}{Proving} & \\multirow{2}{*}{Finding} & \\multirow{2}{*}{Epsilon} & \\multirow{2}{*}{$h/C^*$} & \\multirow{2}{*}{GDRC} '
    for weight in WEIGHTS[1:]:
        latex_str += f' & \\multicolumn{{2}}{{c}}{{{weight}}}'
    latex_str += ' \\\\\n'
    for i in range(len(WEIGHTS[1:])):
        latex_str += f'\\cmidrule(lr){{{6 + 2 * i}-{7 + 2 * i}}}'
    latex_str += '\n& & & &'
    for _ in WEIGHTS[1:]:
        latex_str += ' & \multicolumn{1}{c}{Exp.} & \multicolumn{1}{c}{Qual.}'
    latex_str += '\\\\\n\\midrule\n'

    # Iterate over each row and print column names
    for _, row in pivot.iterrows():
        ho = row[('heuristic-optimal', '')]
        hg = row[('heuristic-greedy', '')]
        epsilon = row[('epsilon', '')]
        subset_df = h_df[(h_df["heuristic-optimal"] == ho) & (h_df["heuristic-greedy"] == hg)]
        subset_df = subset_df.sort_values(by='id', ascending=True)
        heuristic_values = epsilon * subset_df['init-ho'] + (1 - epsilon) * subset_df['init-hg']
        tau, _ = kendalltau(solution_list, heuristic_values)

        hdiff = sum([hv / sc for hv, sc in zip(heuristic_values, solution_list)]) / len(heuristic_values)
        latex_str += f'{ho} & {hg} & {round_half_up(epsilon, 2)} & {round_half_up(hdiff, 3)} & {round_half_up(tau, 3)}'
        for weight in WEIGHTS[1:]:
            if row[('id', weight)] == 100:
                latex_str += f" & {round_half_up(row[('expanded', weight)], 0):,} & {round_half_up(row[('quality', weight)], 3):,}"
            else:
                latex_str += f" & \multicolumn{{2}}{{c}}{{\#{row[('id', weight)]}}}"
        latex_str += ' \\\\\n'

    latex_str += '\\bottomrule\n\\end{tabular}'
    with open('results/latex/stp_ios_table.tex', 'w+') as f:
        f.write(latex_str)


def main():
    data_dir = r"data/stp"
    Path("results").mkdir(exist_ok=True)
    print("Loading data")
    result_df, h_df = parse_dir(data_dir)
    print("Verifying optimal solutions")
    id_to_solution = get_optimal_solutions(result_df)
    print("Adding and verifying solution quality")
    add_solution_quality(result_df, id_to_solution)
    print("Verifying heuristic admissibility")
    verify_heuristics(h_df, id_to_solution)
    print("Generating Excel")
    write_to_excel(result_df, h_df)
    print("Generating LaTex tabular code")
    Path("results/latex").mkdir(exist_ok=True)
    solution_list = [id_to_solution[i] for i in range(100)]
    gen_wa_table_latex(result_df, h_df, solution_list)
    gen_ios_table_latex(result_df, h_df, solution_list)


if __name__ == '__main__':
    WEIGHTS = [1, 1.2, 1.5, 2, 5, 10, 20, 50]
    main()
