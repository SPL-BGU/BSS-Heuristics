//
// Created by Lior Siag on 09/02/2025.
//

#ifndef SRC_PAPER_GBDS_H
#define SRC_PAPER_GBDS_H

#include "AStarOpenClosed.h"
#include "TemplateAStar.h"
#include <iostream>

namespace GBFS {
template<class state, bool lowg = true>
struct GbfsCompare {
    // returns true if i2 is preferred over i1
    bool operator()(const AStarOpenClosedDataWithF<state> &i1, const AStarOpenClosedDataWithF<state> &i2) const {
        if (fequal(i1.h, i2.h)) {
            return lowg ? (fgreater(i1.g, i2.g)) : (fless(i1.g, i2.g));
        }
        return fgreater(i1.h, i2.h);
    }
};

template<typename state, typename action, typename environment, bool lowg = true>
using GBFS = TemplateAStar<state, action, environment, AStarOpenClosed<state, GBFS::GbfsCompare<state, lowg>, AStarOpenClosedDataWithF<state>>>;
}

#endif //SRC_PAPER_GBDS_H
