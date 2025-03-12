//
// Created by Lior Siag on 26/01/2025.
//

#include "WeightedStpDriver.h"
#include "MNPuzzle.h"
#include "BalanceHeuristic.h"
#include "STPInstances.h"
#include "TemplateAStar.h"
#include "GBFS.h"
#include "IOS.h"

namespace balance_wstp {

std::unique_ptr<Heuristic<MNPuzzleState<4, 4>>>
getHeuristic(const std::string &heuristic, const MNPuzzleState<4, 4> &goal) {
    if (heuristic == "md") {
        return std::make_unique<MNPuzzle<4, 4>>();
    } else if (heuristic == "wmd") {
        auto h = std::make_unique<MNPuzzle<4, 4>>();;
        h->SetWeighted(kHeavy);
        return h;
    } else {
        throw std::invalid_argument("Unknown heuristic in WSTP");
    }
}

std::unique_ptr<BalanceHeuristic<MNPuzzleState<4, 4>>>
getBalanceTohHeuristic(const ArgParameters &ap, const MNPuzzleState<4, 4> &goal) {
    return std::make_unique<BalanceHeuristic<MNPuzzleState<4, 4>>>(getHeuristic(ap.heuristic_optimal, goal),
                                                                   getHeuristic(ap.heuristic_greedy, goal),
                                                                   ap.epsilon);
}

void testWeightedStp(const ArgParameters &ap) {
    std::cout << "[D] domain: " << ap.domain
              << "; heuristic-optimal: " << ap.heuristic_optimal
              << "; heuristic-greedy: " << ap.heuristic_greedy
              << "; weight: " << ap.weight
              << "; epsilon: " << ap.epsilon << std::endl;

    MNPuzzleState<4, 4> goal;
    auto heuristic = getBalanceTohHeuristic(ap, goal);
    std::vector<MNPuzzleState<4, 4>> solutionPath;
    MNPuzzle<4, 4> env;
    env.SetWeighted(kHeavy);
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
            timer.StartTimer();
            gbfs.GetPath(&env, start, goal, solutionPath);
            timer.EndTimer();
            printf("[R] alg: gbfs; solution: %1.0f; expanded: %llu; time: %1.6fs\n",
                   env.GetPathLength(solutionPath), gbfs.GetNodesExpanded(), timer.GetElapsedTime());
        }
        if (ap.hasAlgorithm("IOS")) {
            ImprovedOptimisticSearch <MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>> ios;
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
