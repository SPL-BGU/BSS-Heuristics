//
// Created by Lior Siag on 30/12/2024.
//

#include "StpDriver.h"
#include "MNPuzzle.h"
#include "BalanceHeuristic.h"
#include "STPInstances.h"
#include "TemplateAStar.h"
#include "GBFS.h"
#include "IOS.h"

namespace balance_stp {
const std::vector<int> VERTICAL78_PATTERN[2] = {
        {0, 1, 4, 5, 8, 9,  12, 13},
        {0, 2, 3, 6, 7, 10, 11, 14, 15}
};

const std::vector<int> RIDGE_PATTERN[2] = {
        {0, 1, 2, 4,  5,  6,  8,  9},
        {0, 3, 7, 10, 11, 12, 13, 14, 15}
};

const std::vector<int> TEST_PATTERN[2] = {
        {0, 1, 4, 5, 8},
        {0, 2, 3, 6, 7}
};


std::string getPdbName(const MNPuzzleState<4, 4> &goal, const std::string &heuristic, int pid) {
    return "stp_" + heuristic + "_" + std::to_string(std::hash<MNPuzzleState<4, 4>>{}(goal)) + "_" +
           std::to_string(pid) + ".lex";
}

LexPermutationPDB<MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>> *
getPartialPdb(const MNPuzzleState<4, 4> &goal, const std::string &heuristic, int pid, const std::string &pdb_prefix) {
    MNPuzzle<4, 4> env;
    std::vector<int> pattern;
    if (heuristic == "vertical") { pattern = VERTICAL78_PATTERN[pid]; }
    else if (heuristic == "test") { pattern = TEST_PATTERN[pid]; }
    else if (heuristic == "ridge") { pattern = RIDGE_PATTERN[pid]; }
    else {
        std::cerr << "Error: Unknown STP PDB: " << heuristic << std::endl;
        exit(EXIT_FAILURE);
    }
    env.SetPattern(pattern);
    auto pdb = new LexPermutationPDB<MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>>(&env, goal, pattern);

    std::string fileName = pdb_prefix + getPdbName(goal, heuristic, pid);
    if (access(fileName.c_str(), F_OK) != -1) { // Load PDB
        FILE *f = fopen(fileName.c_str(), "r");
        if (!pdb->Load(f)) {
            std::cerr << "Error: Loading PDB failure" << std::endl;
            exit(1);
        }
        fclose(f);
    } else { // Build and save PDB
        pdb->BuildAdditivePDB(goal, (int) std::thread::hardware_concurrency());
        FILE *f = fopen(fileName.c_str(), "w+");
        pdb->Save(f);
        fclose(f);
    }
    return pdb;
}

std::unique_ptr<Heuristic<MNPuzzleState<4, 4>>>
getHeuristic(const std::string &heuristic, const MNPuzzleState<4, 4> &goal, const std::string &pdb_prefix) {
    if (heuristic == "zero") {
        return std::make_unique<ZeroHeuristic<MNPuzzleState<4, 4>>>();
    }
    if ((heuristic.back() == '0' || heuristic.back() == '1')) {
        int pid = heuristic.back() - '0';
        return std::unique_ptr<Heuristic<MNPuzzleState<4, 4>>>(
                getPartialPdb(goal, heuristic.substr(0, heuristic.size() - 1), pid, pdb_prefix));
    }
    auto h = std::make_unique<Heuristic<MNPuzzleState<4, 4>>>();
    h->lookups.resize(0);
    h->lookups.push_back({kAddNode, 1, 2});
    h->lookups.push_back({kLeafNode, 0, 0});
    h->lookups.push_back({kLeafNode, 1, 1});
    h->heuristics.resize(0);
    h->heuristics.emplace_back(getPartialPdb(goal, heuristic, 0, pdb_prefix));
    h->heuristics.emplace_back(getPartialPdb(goal, heuristic, 1, pdb_prefix));
    return h;
}

std::unique_ptr<BalanceHeuristic<MNPuzzleState<4, 4>>>
getBalanceTohHeuristic(const ArgParameters &ap, const MNPuzzleState<4, 4> &goal) {
    return std::make_unique<BalanceHeuristic<MNPuzzleState<4, 4>>>(getHeuristic(ap.heuristic_optimal, goal, ap.pdb),
                                                                   getHeuristic(ap.heuristic_greedy, goal, ap.pdb),
                                                                   ap.epsilon);
}


void testStp(const ArgParameters &ap) {
    std::cout << "[D] domain: " << ap.domain
              << "; heuristic-optimal: " << ap.heuristic_optimal
              << "; heuristic-greedy: " << ap.heuristic_greedy
              << "; weight: " << ap.weight
              << "; epsilon: " << ap.epsilon << std::endl;

    MNPuzzleState<4, 4> goal;
    auto heuristic = getBalanceTohHeuristic(ap, goal);
    std::vector<MNPuzzleState<4, 4>> solutionPath;
    MNPuzzle<4, 4> env;
    Timer timer;

    for (int i: ap.instances) {
        MNPuzzleState<4, 4> start = STP::GetKorfInstance(i);
        std::cout << "[I] id: " << i << "; instance: " << start << std::endl;
        if (ap.norun) {
            printf("[R] alg: heuristic; init-ho: %1.0f; init-hg: %1.0f\n",
                   heuristic->HOptimalCost(start, goal),
                   heuristic->HGreedyCost(start, goal));
            continue;
        }
        if (ap.hasAlgorithm("WA")) {
            TemplateAStar<MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>> astar;
            astar.SetHeuristic(heuristic.get());
            astar.SetWeight(ap.weight);
            timer.StartTimer();
            astar.GetPath(&env, start, goal, solutionPath);
            timer.EndTimer();
            printf("[R] alg: wa; solution: %1.0f; expanded: %llu; time: %1.6fs\n",
                   env.GetPathLength(solutionPath), astar.GetNodesExpanded(), timer.GetElapsedTime());
        }
        if (ap.hasAlgorithm("GBFS")) {
            GBFS::GBFS<MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>> gbfs;
            gbfs.SetHeuristic(heuristic.get());
            gbfs.SetWeight(ap.weight);
            timer.StartTimer();
            gbfs.GetPath(&env, start, goal, solutionPath);
            timer.EndTimer();
            printf("[R] alg: gbfs; solution: %1.0f; expanded: %llu; time: %1.6fs\n",
                   env.GetPathLength(solutionPath), gbfs.GetNodesExpanded(), timer.GetElapsedTime());
        }
        if (ap.hasAlgorithm("IOS")) {
            ImprovedOptimisticSearch<MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>> ios;
            ios.SetGreedyHeuristic(heuristic.get());
            ios.SetOptimalHeuristic(heuristic->GetOptimalHeuristic());
            ios.SetOptimalityBound(ap.weight);
            double weight = 2 * ap.weight - 1;
            ios.SetWeight(weight);
            ios.SetPhi(([=](double x, double y) { return y / (weight) + x; }));
            timer.StartTimer();
            ios.GetPath(&env, start, goal, solutionPath);
            timer.EndTimer();
            printf("[R] alg: ios; solution: %1.0f; expanded: %llu; time: %1.6fs\n", env.GetPathLength(solutionPath),
                   ios.GetNodesExpanded(), timer.GetElapsedTime());
        }
    }

}
}
