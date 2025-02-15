#include <iostream>
#include "ArgParameters.h"
#include "TohDriver.h"
#include "StpDriver.h"
#include "WeightedStpDriver.h"
#include "MNPuzzle.h"
#include "STPInstances.h"

void printRunLine(int argc, char *argv[]) {
    std::cout << "[L] ";
    for (int i = 0; i < argc - 1; ++i) {
        std::cout << argv[i] << " ";
    }
    std::cout << argv[argc - 1] << std::endl;
}

void test(){
    MNPuzzle<4, 4> env;
    MNPuzzle<4, 4> henv;
    henv.SetWeighted(kHeavy);
    MNPuzzleState<4, 4> goal;
    for (int i = 0; i < 100; ++i) {
        MNPuzzleState<4, 4> start = STP::GetKorfInstance(i);
        std::cout << i << "," << env.HCost(start,goal) << "," << henv.HCost(start,goal) << std::endl;
    }
    exit(0);
}

int main(int argc, char *argv[]) {
    printRunLine(argc, argv);
    ArgParameters ap(argc, argv);
    if (ap.domain.substr(0, 3) == "toh") {
        balance_toh::testToh(ap);
    } else if (ap.domain.substr(0, 4) == "wstp") {
        balance_wstp::testWeightedStp(ap);
    } else if (ap.domain.substr(0, 3) == "stp") {
        balance_stp::testStp(ap);
    } else {
        std::cerr << "Error: Unknown domain: " << ap.domain << std::endl;
        exit(EXIT_FAILURE);
    }
}
