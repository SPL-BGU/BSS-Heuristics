import itertools
import math
from decimal import Decimal, ROUND_HALF_UP
from os import PathLike
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame
from scipy.stats import kendalltau

DISTANCES = [57, 55, 59, 56, 56, 52, 52, 50, 46, 59, 57, 45, 46, 59, 62, 42, 66, 55, 46, 52, 54, 59, 49, 54, 52, 58,
             53, 52, 54, 47, 50, 59, 60, 52, 55, 52, 58, 53, 49, 54, 54, 42, 64, 50, 51, 49, 47, 49, 59, 53, 56, 56,
             64, 56, 41, 55, 50, 51, 57, 66, 45, 57, 56, 51, 47, 61, 50, 51, 53, 52, 44, 56, 49, 56, 48, 57, 54, 53,
             42, 57, 53, 62, 49, 55, 44, 45, 52, 65, 54, 50, 57, 57, 46, 53, 50, 49, 44, 54, 57, 54]

SOLUTIONS = [461, 389, 418, 429, 436, 392, 383, 402, 324, 429, 432, 340, 365, 446, 479, 321, 526, 463, 368, 400, 376,
             467, 384, 425, 387, 461, 428, 427, 443, 386, 400, 398, 475, 360, 457, 377, 447, 425, 378, 424, 363, 313,
             510, 378, 394, 373, 406, 348, 460, 370, 427, 446, 512, 419, 325, 365, 376, 394, 443, 519, 316, 464, 401,
             403, 313, 460, 368, 382, 401, 424, 321, 428, 350, 463, 354, 456, 430, 397, 314, 436, 444, 494, 388, 416,
             316, 325, 355, 510, 385, 396, 421, 412, 353, 383, 373, 376, 325, 408, 409, 377]


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


def add_solution_quality(df):
    df['quality'] = df.apply(lambda row: row['solution'] / SOLUTIONS[row['id']], axis=1)
    verify_quality(df)
    return df


def verify_quality(df):
    if not (((df['quality'] >= 1) & (df['quality'] <= df['weight'])) | (df['alg'] == 'gbfs')).all():
        raise ValueError("Some rows have 'quality' not between 1 and 'weight'.")


def verify_heuristics(df):
    if not ((df['init-ho'] <= df['id'].astype(int).apply(lambda x: SOLUTIONS[x])) &
            (df['init-hg'] <= df['id'].astype(int).apply(lambda x: SOLUTIONS[x]))).all():
        raise ValueError("Some heuristics are not admissible.")


def calc_heuristics_stats(df):
    epsilons = [0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1]
    optimal_heuristics = ['wmd']
    greedy_heuristics = ['md']
    for ho, hg in zip(optimal_heuristics, greedy_heuristics):
        for epsilon in epsilons:
            subset_df = df[(df["heuristic-optimal"] == ho) & (df["heuristic-greedy"] == hg)]
            subset_df = subset_df.sort_values(by='id', ascending=True)
            heuristic_values = epsilon * subset_df['init-ho'] + (1 - epsilon) * subset_df['init-hg']
            tau, _ = kendalltau(DISTANCES, heuristic_values)
            hdiff = sum([hv / sc for hv, sc in zip(heuristic_values, SOLUTIONS)]) / len(heuristic_values)
            print(
                f'{ho} & {hg} & {round_half_up(epsilon, 2)} & {round_half_up(hdiff, 3)} & {round_half_up(tau, 3)}\\\\')


def expansions_table(df):
    summary = df.groupby(['alg', 'heuristic-optimal', 'heuristic-greedy', 'weight', 'epsilon'])[
        ['expanded', 'quality']].mean().reset_index()
    for _, row in summary.iterrows():
        print(
            f"{row['alg']} & {row['heuristic-optimal']} & {row['heuristic-greedy']} & {row['weight']} & {round_half_up(row['epsilon'], 2)} & {round_half_up(row['expanded'], 0):,} & {round_half_up(row['quality'], 3)}\\\\")


def gen_wa_table_latex(result_df, h_df):
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
        tau, _ = kendalltau(DISTANCES, heuristic_values)
        hdiff = sum([hv / sc for hv, sc in zip(heuristic_values, SOLUTIONS)]) / len(heuristic_values)
        latex_str += f'{ho} & {hg} & {round_half_up(epsilon, 2)} & {round_half_up(hdiff, 3)} & {round_half_up(tau, 3)}'
        for weight in WEIGHTS:
            if ('id', weight) in row:
                if row[('id', weight)] == 100:
                    latex_str += f" & {round_half_up(row[('expanded', weight)], 0):,} & {round_half_up(row[('quality', weight)], 3):,}"
                else:
                    value = row[('id', weight)]
                    int_value = 0 if math.isnan(value) else int(value)
                    latex_str += f" & \multicolumn{{2}}{{c}}{{\#{int_value}}}"
            else:
                latex_str += f" & \multicolumn{{2}}{{c}}{{\#0}}"
        gbfs_result = gbfs_pivot.loc[(gbfs_pivot.index.get_level_values('epsilon') == epsilon) &
                                     (gbfs_pivot.index.get_level_values('heuristic-optimal') == ho) &
                                     (gbfs_pivot.index.get_level_values('heuristic-greedy') == hg)]
        gbfs_expanded = round_half_up(gbfs_result['expanded'].iloc[0], 0)
        gbfs_quality = round_half_up(gbfs_result['quality'].iloc[0], 3)
        latex_str += f" & {gbfs_expanded:,} & {gbfs_quality}"
        latex_str += ' \\\\\n'
    latex_str += '\\bottomrule\n\\end{tabular}'
    with open('results/latex/wstp_wa.tex', 'w+') as f:
        f.write(latex_str)


def gen_ios_table_latex(result_df, h_df):
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
        tau, _ = kendalltau(DISTANCES, heuristic_values)

        hdiff = sum([hv / sc for hv, sc in zip(heuristic_values, SOLUTIONS)]) / len(heuristic_values)
        latex_str += f'{ho} & {hg} & {round_half_up(epsilon, 2)} & {round_half_up(hdiff, 3)} & {round_half_up(tau, 3)}'
        for weight in WEIGHTS[1:]:
            if row[('id', weight)] == 100:
                latex_str += f" & {round_half_up(row[('expanded', weight)], 0):,} & {round_half_up(row[('quality', weight)], 3):,}"
            else:
                latex_str += f" & \multicolumn{{2}}{{c}}{{\#{row[('id', weight)]}}}"
        latex_str += ' \\\\\n'

    latex_str += '\\bottomrule\n\\end{tabular}'

    with open('results/latex/wstp_ios_table.tex', 'w+') as f:
        f.write(latex_str)


def write_to_excel(result_df, h_df, filename="results/wstp.xlsx"):
    with pd.ExcelWriter(filename) as writer:
        result_df.to_excel(writer, sheet_name="results", index=False)
        h_df.to_excel(writer, sheet_name="heuristics", index=False)


def generate_ios_figure(df, expanded=True, legend=True):
    ios_df = df[df["alg"] == 'ios']
    column = 'expanded' if expanded else 'quality'
    result = {
        eps: group.groupby("weight").filter(lambda g: g["id"].count() == 100).groupby("weight")[column].mean().to_dict()
        for eps, group in ios_df.groupby("epsilon")
    }

    all_weights = ['1', '1.2', '1.5', '2', '5', '10', '20', '50']

    colors = ['#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#72CE6F']
    linestyles = ['-', '--', '-.', ':']
    markers = ['o', 's', 'D', '^', 'v', '*', 'x', 'P', 'H', '+']

    style_cycler = zip(itertools.cycle(colors),
                       itertools.cycle(linestyles),
                       itertools.cycle(markers))

    plt.figure(figsize=(12, 5))

    for (eps, data), (color, ls, marker) in zip(result.items(), style_cycler):
        y = [data.get(float(w), None) for w in all_weights]
        plt.plot(all_weights, y, label=f"ε={eps}", color=color,
                 linestyle=ls, marker=marker, markersize=14, linewidth=4)

    plt.xlabel('Suboptimality Bound', fontsize=26, fontweight='bold')
    if expanded:
        plt.margins(x=0.003)
        plt.ylim(ymin=10 ** 3, ymax=10 ** 6)
        plt.yscale('log')
    else:
        plt.margins(x=0.003)
        plt.ylim(ymin=0.990)

    plt.xticks(fontsize=22, fontweight='bold')
    plt.yticks(fontsize=22, fontweight='bold')

    plt.ylabel(column.capitalize(), fontsize=26, fontweight='bold')
    if legend:
        plt.legend(frameon=True, ncol=2, prop={'size': 22, 'weight': 'bold'})
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'results/figures/wstp_ios_{"expanded" if expanded else "quality"}.pdf')


def generate_wa_figure(df, expanded=True, legend=True):
    wa_df = df[df["alg"] == 'wa']
    gbfs_df = df[df["alg"] == 'gbfs']
    column = 'expanded' if expanded else 'quality'
    result = {}
    for eps, group in wa_df.groupby("epsilon"):
        eps_result = group.groupby("weight").filter(lambda g: g["id"].count() == 100).groupby("weight")[
            column].mean().to_dict()
        eps_result = {str(int(k) if int(k) == k else k): v for k, v in eps_result.items()}
        gbfs_group = gbfs_df[gbfs_df["epsilon"] == eps]
        if gbfs_group["id"].count() == 100:
            eps_result["gbfs"] = gbfs_group[column].mean()
        result[eps] = eps_result

    all_weights = ['1', '1.2', '1.5', '2', '5', '10', '20', '50', 'GBFS']

    colors = ['#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#72CE6F']
    linestyles = ['-', '--', '-.', ':']
    markers = ['o', 's', 'D', '^', 'v', '*', 'x', 'P', 'H', '+']

    style_cycler = zip(itertools.cycle(colors),
                       itertools.cycle(linestyles),
                       itertools.cycle(markers))

    plt.figure(figsize=(12, 5))

    for (eps, data), (color, ls, marker) in zip(result.items(), style_cycler):
        y = [data.get(w.lower(), None) for w in all_weights]
        plt.plot(all_weights, y, label=f"ε={eps}", color=color,
                 linestyle=ls, marker=marker, markersize=14, linewidth=4)

    plt.xlabel('Suboptimality Bound', fontsize=26, fontweight='bold')
    if expanded:
        plt.margins(x=0.003)
        plt.ylim(ymin=10 ** 3, ymax=10 ** 7)
        plt.yscale('log')
    else:
        plt.margins(x=0.003)
        plt.ylim(ymin=0.990)

    plt.xticks(fontsize=22, fontweight='bold')
    plt.yticks(fontsize=22, fontweight='bold')

    plt.ylabel(column.capitalize(), fontsize=26, fontweight='bold')
    if legend:
        plt.legend(frameon=True, ncol=2, prop={'size': 22, 'weight': 'bold'})
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'results/figures/wstp_wa_{"expanded" if expanded else "quality"}.pdf')


def main():
    data_dir = r"data/wstp"
    Path("results").mkdir(exist_ok=True)
    print("Loading data")
    result_df, h_df = parse_dir(data_dir)
    print("Adding and verifying solution quality")
    add_solution_quality(result_df)
    print("Verifying heuristic admissibility")
    verify_heuristics(h_df)
    print("Generating Excel")
    write_to_excel(result_df, h_df)
    print("Generating LaTex tabular code")
    Path("results/latex").mkdir(exist_ok=True)
    gen_wa_table_latex(result_df, h_df)
    gen_ios_table_latex(result_df, h_df)
    print("Generating figures")
    generate_wa_figure(result_df, True, False)
    generate_wa_figure(result_df, False, False)
    generate_ios_figure(result_df, True, False)
    generate_ios_figure(result_df, False, True)


if __name__ == '__main__':
    WEIGHTS = [1, 1.2, 1.5, 2, 5, 10, 20, 50]
    main()
