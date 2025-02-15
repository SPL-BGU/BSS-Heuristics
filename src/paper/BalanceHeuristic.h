//
// Created by Lior Siag on 29/12/2024.
//

#ifndef SRC_PAPER_BALANCEHEURISTIC_H
#define SRC_PAPER_BALANCEHEURISTIC_H


#include <memory>
#include "Heuristic.h"

template<class state>
class BalanceHeuristic : public Heuristic<state> {
public:
    BalanceHeuristic(std::unique_ptr<Heuristic<state>> heuristic_optimal,
                     std::unique_ptr<Heuristic<state>> heuristic_greedy,
                     double epsilon) : heuristic_optimal(std::move(heuristic_optimal)),
                                       heuristic_greedy(std::move(heuristic_greedy)), epsilon(epsilon) {}

    ~BalanceHeuristic() override {
        for (int i = 0; i < heuristic_greedy->heuristics.size(); ++i) {
            delete heuristic_greedy->heuristics[i];
        }

        for (int i = 0; i < heuristic_optimal->heuristics.size(); ++i) {
            delete heuristic_optimal->heuristics[i];
        }
    }

    double HCost(const state &a, const state &b) const override {
        return epsilon * heuristic_optimal->HCost(a, b) + (1 - epsilon) * heuristic_greedy->HCost(a, b);
    }

    double HOptimalCost(const state &a, const state &b) const{
        return heuristic_optimal->HCost(a, b);
    }

    double HGreedyCost(const state &a, const state &b) const{
        return heuristic_greedy->HCost(a, b);
    }

protected:
    std::unique_ptr<Heuristic<state>> heuristic_optimal;
    std::unique_ptr<Heuristic<state>> heuristic_greedy;
    double epsilon;
};

#endif //SRC_PAPER_BALANCEHEURISTIC_H
