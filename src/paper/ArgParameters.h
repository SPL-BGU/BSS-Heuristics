//
// Created by Lior Siag on 29/12/2024.
//

#ifndef SRC_PAPER_ARGPARAMETERS_H
#define SRC_PAPER_ARGPARAMETERS_H


#include <string>
#include <vector>
#include <iostream>
#include <algorithm>

class ArgParameters {
public:
    ArgParameters(int argc, char *argv[]) {
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--help") {
                ArgParameters::help();
            } else if (arg == "-d" || arg == "--domain") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                this->domain = argv[i];
            } else if (arg == "-ho" || arg == "--heuristic-optimal") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                this->heuristic_optimal = argv[i];
            } else if (arg == "-hg" || arg == "--heuristic-greedy") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                this->heuristic_greedy = argv[i];
            } else if (arg == "-i" || arg == "--instances") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                std::vector<std::string> lineInstances;
                while (i < argc && argv[i][0] != '-') {
                    lineInstances.emplace_back(argv[i]);
                    ++i;
                }
                --i; // Adjust for the loop increment
                this->parseInstanceRanges(lineInstances);
            } else if (arg == "-e" || arg == "--epsilon") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                std::string epsstr = argv[i];
                size_t pos = epsstr.find('/');
                if (pos == std::string::npos) {
                    this->epsilon = std::stod(argv[i]);
                } else {
                    double x = std::stod(epsstr.substr(0, pos));
                    double y = std::stod(epsstr.substr(pos + 1));
                    this->epsilon = x / y;
                }

            } else if (arg == "-w" || arg == "--weight") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                this->weight = std::stod(argv[i]);
            } else if (arg == "-a" || arg == "--algorithms") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                while (i < argc && argv[i][0] != '-') {
                    this->algs.emplace_back(argv[i]);
                    ++i;
                }
                --i; // Adjust for the loop increment
            } else if (arg == "-p" || arg == "--pdb") {
                ArgParameters::verifyValidFlagValue(argc, argv, ++i);
                this->pdb = argv[i];
                if (this->pdb.back() != '/') {
                    this->pdb += '/';
                }
            } else {
                std::cerr << "Error: Unknown argument: " << arg << std::endl;
                exit(EXIT_FAILURE);
            }
        }

        // Lowercase domain and heuristic, so it's easier to work with them later
        std::transform(this->domain.begin(), this->domain.end(), this->domain.begin(),
                       [](unsigned char c) { return std::tolower(c); });
        std::transform(this->heuristic_optimal.begin(), this->heuristic_optimal.end(), this->heuristic_optimal.begin(),
                       [](unsigned char c) { return std::tolower(c); });
        std::transform(this->heuristic_greedy.begin(), this->heuristic_greedy.end(), this->heuristic_greedy.begin(),
                       [](unsigned char c) { return std::tolower(c); });

        if (weight < 1) {
            std::cerr << "Missing or invalid value for weight" << std::endl;
            exit(EXIT_FAILURE);
        }

        if (epsilon < 0 || epsilon > 1) {
            std::cerr << "Missing or invalid value for epsilon" << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    bool hasAlgorithm(const std::string &alg) const {
        return std::find(algs.begin(), algs.end(), alg) != algs.end();
    }

    void parseInstanceRanges(const std::vector<std::string> &input) {
        for (const std::string &part: input) {
            size_t dashPos = part.find('-');

            if (dashPos == std::string::npos) {
                // It's a single number
                try {
                    int number = std::stoi(part);
                    this->instances.push_back(number);
                } catch (const std::invalid_argument &e) {
                    std::cerr << "Error: Invalid instance: " << part << std::endl;
                    exit(EXIT_FAILURE);
                }
            } else {
                // It's a range
                try {
                    int start = std::stoi(part.substr(0, dashPos));
                    int end = std::stoi(part.substr(dashPos + 1));

                    if (start >= end) {
                        std::cerr << "Error: Invalid range: " << part << std::endl;
                        exit(EXIT_FAILURE);
                    }

                    for (int i = start; i < end; ++i) {
                        this->instances.push_back(i);
                    }
                } catch (const std::invalid_argument &e) {
                    std::cerr << "Error: Invalid input: " << part << std::endl;
                    exit(EXIT_FAILURE);
                }
            }
        }
    }

    friend std::ostream &operator<<(std::ostream &os, const ArgParameters &params) {
        os << "Domain: " << params.domain << "\n";

        os << "Optimal Heuristic: " << params.heuristic_optimal << "\n";
        os << "Greedy Heuristic: " << params.heuristic_greedy << "\n";

        os << "Algorithms: ";
        for (const auto &alg: params.algs) { os << alg << " "; }
        os << "\n";

        os << "Instances: ";
        for (const auto &instance: params.instances) { os << instance << " "; }
        os << "\n";

        if (params.pdb.empty()) {
            os << "PDB dir not set " << "\n";
        } else {
            os << "PDB dir: " << params.pdb << "\n";
        }

        return os;
    }

    static void help() {
        std::cout << "Usage: program [OPTIONS]\n\n";
        std::cout << "Options:\n";
        std::cout << "  -d, --domain <DOMAIN>          Specify the domain.\n";
        std::cout << "  -i, --instances <R1 R2 R3>       Specify a list of instance ranges (e.g., 1-3 which represents "
                     "[1,3)) or single instances (i.e., 3).\n";
        std::cout << "  -ho, --heuristic-optimal <HEURISTIC>    Specify the optimal heuristic.\n";
        std::cout << "  -hg, --heuristic-greedy <HEURISTIC>    Specify the greedy heuristic.\n";
        std::cout << "  -a, --algorithms <A1 A2 ...>   Specify a list of algorithms.\n";
        std::cout << "  -w, --weights <W1 W2 ...>      Specify a list of heuristic weights.\n";
        std::cout << "  -p, --pdb <DIR>    Specify the directory which contains the PDB files.\n";
        std::cout << "  --help                         Show this help message and exit.\n\n";
        std::cout << "Examples:\n";
        std::cout << "  program --domain planning -i 1-5 7 "
                  << "--heuristic-optimal h1 --heuristic-greedy h2 --algorithms a1 a2\n";
        std::cout << "  program -d logistics -i 10 -h heuristic1 -a algorithm1\n";

        // Exit the program
        std::exit(EXIT_SUCCESS);
    }

    std::string domain;
    std::string heuristic_optimal;
    std::string heuristic_greedy;
    std::vector<std::string> algs;
    std::vector<int> instances;
    double epsilon = -1;
    double weight = -1;
    std::string pdb;

private:
    static void verifyValidFlagValue(int argc, char *argv[], int index) {
        if (index >= argc || argv[index][0] == '-') {
            std::cerr << "Missing values for: " << argv[index - 1] << std::endl;
            exit(EXIT_FAILURE);
        }
    }
};

#endif //SRC_PAPER_ARGPARAMETERS_H
