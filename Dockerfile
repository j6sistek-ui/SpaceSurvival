FROM gcc:14-bookworm
WORKDIR /workspace
COPY Source/SpaceSurvival/Domain/ /workspace/Source/SpaceSurvival/Domain/
COPY Tests/ /workspace/Tests/
RUN g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror -ISource/SpaceSurvival/Domain Source/SpaceSurvival/Domain/SurvivalCore.cpp Tests/CoreTests.cpp -o /workspace/core-tests
RUN g++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -ISource/SpaceSurvival/Domain Source/SpaceSurvival/Domain/SurvivalCore.cpp Tests/CoreTests.cpp -o /workspace/core-sanitized
CMD ["sh", "/workspace/Tests/RunCore.sh"]
