#!/usr/bin/env bash
/*
 * NOTE:
 * The shebang above is a no-op placeholder when compiled; it allows this file
 * to be opened or inspected as a script but has no effect on the compiled
 * binary. You should compile this file with a C++ compiler, for example:
 *
 *   g++ -std=c++11 -Wall -O2 camera_info.cpp -o camera_info
 *
 * Camera / V4L2 device inspection tool in C++.
 *
 * This program is intended for **inspection and understanding**, not image capture.
 *
 * Functionality:
 *  - Enumerates /dev/video* character devices.
 *  - Uses the userspace tool `v4l2-ctl` (from v4l-utils) via subprocess calls.
 *  - Prints clearly labeled sections for each device's capabilities and
 *    supported formats/resolutions.
 *
 * Relationship to kernel drivers and V4L2:
 *  - /dev/video* nodes are created by the Linux kernel's V4L2 (Video4Linux2)
 *    subsystem when a video driver (e.g. `uvcvideo` for USB UVC cameras)
 *    registers a video device.
 *  - `v4l2-ctl` is a userspace utility that communicates with these device
 *    nodes using V4L2 ioctls, exposing what the kernel driver reports about
 *    the underlying hardware.
 *  - This program is a thin wrapper around `v4l2-ctl` to present an
 *    inspection-oriented view of those capabilities.
 */

#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <glob.h>
#include <limits.h>
#include <sys/stat.h>
#include <unistd.h>

#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

bool isCharDevice(const std::string &path) {
    struct stat st {};
    if (stat(path.c_str(), &st) != 0) {
        return false;
    }
    return S_ISCHR(st.st_mode);
}

// Find `v4l2-ctl` in PATH. On success, returns true and fills `outPath`.
bool findV4l2Ctl(std::string &outPath) {
    const char *pathEnv = std::getenv("PATH");
    if (!pathEnv) {
        return false;
    }

    std::string paths(pathEnv);
    std::stringstream ss(paths);
    std::string token;

    while (std::getline(ss, token, ':')) {
        if (token.empty()) {
            continue;
        }

        std::string candidate = token + "/v4l2-ctl";
        if (access(candidate.c_str(), X_OK) == 0) {
            outPath = candidate;
            return true;
        }
    }

    return false;
}

// Run a shell command using popen() and print its stdout to std::cout.
// Returns 0 on success, non-zero on error.
int runCommandAndPrint(const std::string &cmd) {
    FILE *fp = popen(cmd.c_str(), "r");
    if (!fp) {
        std::cerr << "Failed to run command: " << cmd << "\n";
        return -1;
    }

    char line[1024];
    bool printedAny = false;

    while (fgets(line, sizeof(line), fp) != nullptr) {
        std::cout << line;
        printedAny = true;
    }

    if (!printedAny) {
        std::cout << "(no output)\n";
    }

    int status = pclose(fp);
    if (status == -1) {
        std::cerr << "Error closing command stream: " << std::strerror(errno) << "\n";
        return -1;
    }

    return 0;
}

// Inspect a single V4L2 device using v4l2-ctl.
//
// We query:
//  - Overall device information and capabilities (--all)
//  - Supported formats and resolutions (--list-formats-ext)
//
// This shows what the kernel V4L2 driver exposes to userspace and helps
// understand what kinds of pipelines are possible on top.
void inspectDevice(const std::string &v4l2CtlPath, const std::string &device) {
    std::cout << std::string(80, '=') << "\n";
    std::cout << "DEVICE: " << device << "\n";
    std::cout << std::string(80, '=') << "\n\n";

    // Overall device information and capabilities
    std::cout << ">>> BASIC INFORMATION AND CAPABILITIES (v4l2-ctl --all)\n";
    {
        std::ostringstream oss;
        oss << "\"" << v4l2CtlPath << "\" --device=\"" << device << "\" --all";
        runCommandAndPrint(oss.str());
    }
    std::cout << "\n";

    // Extended formats and resolutions
    std::cout << ">>> SUPPORTED FORMATS AND RESOLUTIONS (v4l2-ctl --list-formats-ext)\n";
    {
        std::ostringstream oss;
        oss << "\"" << v4l2CtlPath << "\" --device=\"" << device
            << "\" --list-formats-ext";
        runCommandAndPrint(oss.str());
    }
    std::cout << "\n";

    // Note: We intentionally do NOT perform any frame capture here.
    // The goal is introspection only: understanding what the kernel
    // driver and V4L2 layer make available to higher-level code.
}

}  // namespace

int main() {
    std::string v4l2CtlPath;
    if (!findV4l2Ctl(v4l2CtlPath)) {
        std::cerr
            << "ERROR: `v4l2-ctl` not found in PATH.\n"
            << "Install `v4l-utils` (e.g. `sudo apt-get install v4l-utils`) "
            << "to use this inspection tool.\n";
        return 1;
    }

    std::cout << "Camera / V4L2 Device Inspection (C++ version)\n";
    std::cout << "---------------------------------------------\n\n";
    std::cout << "Context:\n";
    std::cout << "- /dev/video* nodes are exposed by the Linux kernel's V4L2 subsystem.\n";
    std::cout << "- Drivers (e.g. `uvcvideo` for USB cameras) register these devices.\n";
    std::cout << "- This program uses `v4l2-ctl` as a front-end to V4L2 ioctls to report\n";
    std::cout << "  the driver- and hardware-exposed capabilities to userspace.\n\n";

    // Enumerate /dev/video* using glob()
    glob_t g;
    int r = glob("/dev/video*", 0, nullptr, &g);
    if (r != 0 || g.gl_pathc == 0) {
        std::cout << "No /dev/video* devices found. Is a camera connected and recognized?\n";
        globfree(&g);
        return 0;
    }

    std::vector<std::string> devices;
    devices.reserve(g.gl_pathc);

    std::cout << "Discovered video devices:\n";
    for (size_t i = 0; i < g.gl_pathc; ++i) {
        std::string path = g.gl_pathv[i];
        if (!isCharDevice(path)) {
            continue;
        }
        devices.push_back(path);
        std::cout << "  - " << path << "\n";
    }
    std::cout << "\n";

    if (devices.empty()) {
        std::cout << "No character-device /dev/video* nodes found.\n";
        globfree(&g);
        return 0;
    }

    // Inspect each character device
    for (const auto &dev : devices) {
        inspectDevice(v4l2CtlPath, dev);
    }

    globfree(&g);
    return 0;
}


