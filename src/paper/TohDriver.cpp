//
// Created by Lior Siag on 29/12/2024.
//

#include <memory>
#include "TohDriver.h"
#include "TOH.h"
#include "BalanceHeuristic.h"
#include "TemplateAStar.h"

namespace balance_toh {
void unsupportedPdbExit(const std::string &heuristic) {
    std::cerr << "Unsupported ToH PDB size: " << heuristic << std::endl;
    exit(1);
}

template<int N, int SIZE, int OFFSET = 0>
TOHPDB<SIZE, N, OFFSET> *MakePdb(const TOHState<N> &goal) {
    TOH<SIZE> env;
    auto topPdb = new TOHPDB<SIZE, N, OFFSET>(&env, goal);
    topPdb->BuildPDB(goal, (int) std::thread::hardware_concurrency(), false);
    return topPdb;
}

template<int N, int BOTTOM, int TOP = N - BOTTOM>
Heuristic<TOHState<N>> *GetAdditivePdb(const TOHState<N> &goal) {
    auto h = new Heuristic<TOHState<N>>();

    TOH<TOP> envTop;
    TOH<BOTTOM> envBottom;
    auto bottomPdb = new TOHPDB<BOTTOM, N, 0>(&envBottom, goal);
    bottomPdb->BuildPDB(goal, (int) std::thread::hardware_concurrency(), false);

    h->lookups.resize(0);
    h->lookups.push_back({kAddNode, 1, 2});
    h->lookups.push_back({kLeafNode, 0, 0});
    h->lookups.push_back({kLeafNode, 1, 1});
    h->heuristics.resize(0);
    if (TOP == 0) {
        h->heuristics.push_back(new ZeroHeuristic<TOHState<N>>);
    } else {
        auto *topPdb = new TOHPDB<TOP, N, BOTTOM>(&envTop, goal);
        topPdb->BuildPDB(goal, (int) std::thread::hardware_concurrency(), false);
        h->heuristics.push_back(topPdb);
    }
    h->heuristics.push_back(bottomPdb);

    return h;
}

template<int N>
void DestroyAdditivePdb(Heuristic<TOHState<N>> *h) {
    delete h->heuristics[0];
    delete h->heuristics[1];
    delete h;
}

template<int N>
std::unique_ptr<Heuristic<TOHState<N>>> getPdb(const std::string &heuristic, const TOHState<N> &goal) {
    size_t plusPos = heuristic.find('+');
    if (plusPos == std::string::npos) {
        std::cerr << "Missing + in ToH PDB heuristic: " << heuristic << std::endl;
        exit(1);
    }
    int bottomSize = std::stoi(heuristic.substr(0, plusPos));
    int topSize = std::stoi(heuristic.substr(plusPos + 1));

    switch (bottomSize) {
        case 6:
            switch (topSize) {
                case 0:
                    return std::unique_ptr<Heuristic<TOHState<N>>>(GetAdditivePdb<N, 6, 0>(goal));
                case 6:
                    return std::unique_ptr<Heuristic<TOHState<N>>>(GetAdditivePdb<N, 6, 6>(goal));
                default:
                    unsupportedPdbExit(heuristic);
            }
            break;
        case 8:
            switch (topSize) {
                case 0:
                    return std::unique_ptr<Heuristic<TOHState<N>>>(GetAdditivePdb<N, 8, 0>(goal));
                case 4:
                    return std::unique_ptr<Heuristic<TOHState<N>>>(GetAdditivePdb<N, 8, 4>(goal));
                default:
                    unsupportedPdbExit(heuristic);
            }
        case 10:
            switch (topSize) {
                case 0:
                    return std::unique_ptr<Heuristic<TOHState<N>>>(GetAdditivePdb<N, 10, 0>(goal));
                case 2:
                    return std::unique_ptr<Heuristic<TOHState<N>>>(GetAdditivePdb<N, 10, 2>(goal));
                default:
                    unsupportedPdbExit(heuristic);
            }
        default:
            unsupportedPdbExit(heuristic);
    }
}

template<int N>
std::unique_ptr<BalanceHeuristic<TOHState<N>>>
getBalanceTohHeuristic(const std::string &ho, const std::string &hg, double epsilon, const TOHState<N> &goal) {
    return std::make_unique<BalanceHeuristic<TOHState<N>>>(getPdb(ho, goal), getPdb(hg, goal), epsilon);
}

template<int N>
void generateState(TOHState<N> &state, int id) {
    const int table[] = {52058078, 116173544, 208694125, 131936966, 141559500, 133800745, 194246206, 50028346,
                         167007978, 207116816, 163867037, 119897198, 201847476, 210859515, 117688410, 121633885};
    const int table2[] = {145008714, 165971878, 154717942, 218927374, 182772845, 5808407, 19155194, 137438954,
                          13143598, 124513215, 132635260, 39667704, 2462244, 41006424, 214146208, 54305743};
    srandom(table[id & 0xF] ^ table2[(id >> 4) & 0xF]);
    state.counts[0] = state.counts[1] = state.counts[2] = state.counts[3] = 0;
    for (int x = N; x > 0; x--) {
        int whichPeg = random() % 4;
        state.disks[whichPeg][state.counts[whichPeg]] = x;
        state.counts[whichPeg]++;
    }
}

template<int N>
void testToh(const ArgParameters &ap) {
    std::cout << "[D] domain: TOH-" << N
              << "; heuristic-optimal: " << ap.heuristic_optimal
              << "; heuristic-greedy: " << ap.heuristic_greedy
              << "; weight: " << ap.weight
              << "; epsilon: " << ap.epsilon << std::endl;
    TOHState<N> goal;
    auto heuristic = getBalanceTohHeuristic(ap.heuristic_optimal, ap.heuristic_greedy, ap.epsilon, goal);
    std::vector<TOHState<N>> solutionPath;
    TOH<N> env;
    TemplateAStar<TOHState<N>, TOHMove, TOH<N>> astar;
    Timer timer;
    astar.SetHeuristic(heuristic.get());
    astar.SetWeight(ap.weight);
    for (int i: ap.instances) {
        TOHState<N> start;
        generateState(start, i);
        std::cout << "[I] id: " << i << "; instance: " << start << std::endl;
        if (ap.hasAlgorithm("WA")) {
            timer.StartTimer();
            astar.GetPath(&env, start, goal, solutionPath);
            timer.EndTimer();
            printf("[R] alg: wa; solution: %1.0f; expanded: %llu; time: %1.6fs\n", env.GetPathLength(solutionPath),
                   astar.GetNodesExpanded(), timer.GetElapsedTime());
        }
    }
}

void testToh(const ArgParameters &ap) {
    testToh<12>(ap);
}
}
