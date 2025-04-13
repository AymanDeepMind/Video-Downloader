#include <iostream>
#include <filesystem>
#include <string>
#include <cstdio>    // For popen (or _popen on Windows)
#include <cstdlib>
#ifdef _WIN32
    #include <Windows.h>
    #define POPEN _popen
    #define PCLOSE _pclose
#else
    #include <unistd.h>
    #define POPEN popen
    #define PCLOSE pclose
#endif

// Returns the directory where the executable is located.
// On Windows, this uses GetModuleFileName.
// On non-Windows platforms, an alternative (Linux example) is provided.
std::string get_script_dir() {
    #ifdef _WIN32
        char buffer[MAX_PATH];
        if (GetModuleFileNameA(NULL, buffer, MAX_PATH) == 0) {
            std::cerr << "> Error getting module file name." << std::endl;
            std::exit(1);
        }
        std::filesystem::path p(buffer);
        return p.parent_path().string();
    #else
        char result[PATH_MAX];
        ssize_t count = readlink("/proc/self/exe", result, PATH_MAX);
        if (count == -1) {
            std::cerr << "> Error getting executable path." << std::endl;
            std::exit(1);
        }
        std::filesystem::path p(std::string(result, count));
        return p.parent_path().string();
    #endif
}

int main() {
    // Get the directory of the script/executable.
    std::string script_dir = get_script_dir();

    // Construct the full path to yt-dlp.exe using std::filesystem.
    std::filesystem::path yt_dlp_path = std::filesystem::path(script_dir) / "yt-dlp.exe";

    // Check if yt-dlp.exe exists.
    if (!std::filesystem::exists(yt_dlp_path)) {
        std::cout << "> yt-dlp.exe not found." << std::endl;
        std::cout << "> Expected path: " << yt_dlp_path.string() << std::endl;
        std::cout << "\nProcess terminated. Press enter to exit...";
        std::cin.get();
        return 1;
    }

    std::cout << "Checking for yt-dlp updates..." << std::endl;

    // Prepare the command string.
    // If the path contains spaces, enclose it in quotes.
    std::string command = "\"" + yt_dlp_path.string() + "\" -U";

    // Change the working directory to script_dir.
    // This emulates Python's cwd argument in subprocess.
    std::filesystem::current_path(script_dir);

    // Open a pipe to run the command and capture its output.
    FILE* pipe = POPEN(command.c_str(), "r");
    if (!pipe) {
        std::cerr << "Error: Failed to start yt-dlp update process." << std::endl;
        return 1;
    }

    bool update_started = false;
    char lineBuffer[512]; // Buffer to store each output line.

    // Read output line by line.
    while (fgets(lineBuffer, sizeof(lineBuffer), pipe) != nullptr) {
        std::string line(lineBuffer);
        
        // Remove any trailing newline characters.
        line.erase(line.find_last_not_of("\r\n") + 1);

        if (line.empty()) {
            continue;
        }

        // You can uncomment the next line to show every output line.
        // std::cout << "[yt-dlp] > " << line << std::endl;

        if (line.find("Updating to") != std::string::npos) {
            std::cout << "\n> yt-dlp is being updated...\n\n\t- Do not close this window\n\t- Do not use the downloader during the process." << std::endl;
            update_started = true;
        } else if (line.find("yt-dlp is up to date") != std::string::npos) {
            std::cout << "\n> yt-dlp is already up to date. You can close the window." << std::endl;
            break;
        } else if (line.find("Updated yt-dlp to") != std::string::npos) {
            std::cout << "\n> yt-dlp was successfully updated! Now you can close the window and start downloading." << std::endl;
            break;
        }
        // Optionally handle unexpected output here.
    }

    // Close the pipe.
    int returnCode = PCLOSE(pipe);
    if (returnCode != 0) {
        std::cout << "\n> Error: Update process returned code " << returnCode << std::endl;
    }

    // Pause before exit.
    std::cout << "\nPress enter to exit...";
    std::cin.get();

    return 0;
}
