//
// Created by Lior Siag on 26/01/2025.
//

#include "WeightedStpDriver.h"
#include "MNPuzzle.h"
#include "BalanceHeuristic.h"
#include "STPInstances.h"
#include "TemplateAStar.h"

namespace balance_wstp {

std::unique_ptr<Heuristic<MNPuzzleState<4, 4>>>
getHeuristic(const std::string &heuristic, const MNPuzzleState<4, 4> &goal) {
    if(heuristic=="md"){
        return std::make_unique<MNPuzzle<4,4>>();
    } else if (heuristic=="wmd"){
        auto h = std::make_unique<MNPuzzle<4,4>>();;
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
        if (ap.hasAlgorithm("WA")) {
            TemplateAStar<MNPuzzleState<4, 4>, slideDir, MNPuzzle<4, 4>> astar;
            astar.SetHeuristic(heuristic.get());
            astar.SetWeight(ap.weight);
            timer.StartTimer();
            astar.GetPath(&env, start, goal, solutionPath);
            timer.EndTimer();
            printf("[R] alg: wa; solution: %1.0f; init-h: %1.3f; expanded: %llu; time: %1.6fs\n",
                   env.GetPathLength(solutionPath), heuristic->HCost(start, goal),
                   astar.GetNodesExpanded(), timer.GetElapsedTime());
        }
    }
}
}
