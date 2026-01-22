import board from "../assets/images/board.png";

const Rules = () => {
  return (
    <div className="font-sans bg-bg-dark text-text-light w-full h-full overflow-y-auto">
      {/* Header */}
      <section className="bg-bg-surface border-b border-border-muted py-16">
        <div className="container mx-auto px-4 text-center max-w-6xl">
          <h1 className="text-5xl md:text-6xl font-bold text-text-white mb-4 tracking-tight">
            Bagh Chal Rules
          </h1>
          <div className="w-20 h-1 bg-primary mx-auto rounded mb-6"></div>
          <p className="text-xl text-text-muted max-w-3xl mx-auto font-light">
            Master the ancient art of strategic warfare between tigers and goats
          </p>
        </div>
      </section>

      <div className="container mx-auto px-4 py-16 max-w-6xl">
        {/* Game Overview */}
        <section className="mb-16">
          <div className="bg-bg-surface rounded-xl shadow-2xl p-8 mb-8 border border-border-muted">
            <h2 className="text-3xl font-bold text-text-white mb-6">
              Game Overview
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <div className="space-y-6">
                <p className="text-lg text-text-light leading-relaxed">
                  Bagh Chal (Tigers and Goats) is a traditional asymmetric
                  strategy game from Nepal. Two players compete with different
                  pieces and objectives, creating a unique and challenging
                  gameplay experience.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-bg-dark p-5 rounded-lg border border-border-muted">
                    <div className="text-2xl font-bold text-text-white mb-1">
                      4 Tigers
                    </div>
                    <div className="text-sm text-text-muted uppercase tracking-wide">
                      Hunters
                    </div>
                  </div>
                  <div className="bg-bg-dark p-5 rounded-lg border border-border-muted">
                    <div className="text-2xl font-bold text-text-white mb-1">
                      20 Goats
                    </div>
                    <div className="text-sm text-text-muted uppercase tracking-wide">
                      Defenders
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-center">
                <div className="relative bg-bg-dark p-8 rounded-xl border border-border-muted shadow-xl">
                  <img
                    src={board}
                    alt="Bagh Chal game board"
                    className="w-full max-w-80 rounded"
                  />
                  <div className="absolute -top-3 -right-3 bg-primary text-text-white text-xs px-4 py-1 rounded-full font-semibold uppercase tracking-wide">
                    Traditional
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Setup */}
        <section className="mb-16">
          <div className="bg-bg-surface rounded-xl shadow-2xl p-8 border border-border-muted">
            <h2 className="text-3xl font-bold text-text-white mb-6">
              Game Setup
            </h2>
            <div className="space-y-6">
              <div className="bg-bg-dark border-l-4 border-primary p-6 rounded-r-lg">
                <h3 className="text-xl font-semibold text-text-white mb-4">
                  Initial Position
                </h3>
                <ul className="space-y-3 text-text-light">
                  <li className="flex items-start">
                    <span className="text-primary mr-3 mt-1">•</span>
                    <span>
                      4 tigers are placed at the four corner points of the board
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">•</span>
                    <span>
                      All 20 goats start off the board and will be placed during
                      gameplay
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">•</span>
                    <span>The goat player goes first</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Gameplay Phases */}
        <section className="mb-16">
          <div className="bg-[#2f2d2a] rounded-xl shadow-2xl p-8 border border-[#3a3835]">
            <h2 className="text-3xl font-bold text-white mb-6">
              Gameplay Phases
            </h2>

            <div className="space-y-8">
              {/* Phase 1 */}
              <div className="border-l-4 border-[#f95e5e] bg-[#262522] p-6 rounded-r-lg">
                <h3 className="text-2xl font-semibold text-white mb-4">
                  Phase 1: Placement Phase
                </h3>
                <div className="space-y-4">
                  <p className="text-gray-300 text-lg">
                    The first phase focuses on positioning. Goats enter the
                    battlefield one by one.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-[#2f2d2a] p-5 rounded-lg border border-[#3a3835]">
                      <h4 className="font-semibold text-white mb-3 text-lg">
                        🐐 Goat Turn:
                      </h4>
                      <ul className="space-y-2 text-gray-300">
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Place one goat on any empty intersection</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Cannot move existing goats yet</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Try to limit tiger movement</span>
                        </li>
                      </ul>
                    </div>
                    <div className="bg-[#2f2d2a] p-5 rounded-lg border border-[#3a3835]">
                      <h4 className="font-semibold text-white mb-3 text-lg">
                        🐅 Tiger Turn:
                      </h4>
                      <ul className="space-y-2 text-gray-300">
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Move one tiger to adjacent empty point</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Can capture goats by jumping over them</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Focus on creating capture opportunities</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                  <div className="bg-[#2f2d2a] p-4 rounded-lg border border-[#3a3835]">
                    <p className="text-gray-300">
                      ⏱️ This phase ends when all 20 goats have been placed on
                      the board
                    </p>
                  </div>
                </div>
              </div>

              {/* Phase 2 */}
              <div className="border-l-4 border-[#f95e5e] bg-[#262522] p-6 rounded-r-lg">
                <h3 className="text-2xl font-semibold text-white mb-4">
                  Phase 2: Movement Phase
                </h3>
                <div className="space-y-4">
                  <p className="text-gray-300 text-lg">
                    Now both tigers and goats can move freely. The real
                    strategic battle begins!
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-[#2f2d2a] p-5 rounded-lg border border-[#3a3835]">
                      <h4 className="font-semibold text-white mb-3 text-lg">
                        🐐 Goat Movement:
                      </h4>
                      <ul className="space-y-2 text-gray-300">
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>
                            Move one goat to adjacent empty intersection
                          </span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Work together to surround tigers</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Block tiger escape routes</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Protect vulnerable goats</span>
                        </li>
                      </ul>
                    </div>
                    <div className="bg-[#2f2d2a] p-5 rounded-lg border border-[#3a3835]">
                      <h4 className="font-semibold text-white mb-3 text-lg">
                        🐅 Tiger Movement:
                      </h4>
                      <ul className="space-y-2 text-gray-300">
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Move to adjacent empty point, OR</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Jump over adjacent goat to capture it</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Continue hunting for the 5th goat</span>
                        </li>
                        <li className="flex items-start">
                          <span className="text-[#f95e5e] mr-2">•</span>
                          <span>Avoid getting completely surrounded</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Movement Rules */}
        <section className="mb-16">
          <div className="bg-[#2f2d2a] rounded-xl shadow-2xl p-8 border border-[#3a3835]">
            <h2 className="text-3xl font-bold text-white mb-6">
              Movement Rules
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="bg-[#262522] border border-[#3a3835] p-6 rounded-lg">
                  <h3 className="text-xl font-semibold text-white mb-4">
                    🐅 Tiger Movement
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-[#f95e5e] mb-2">
                        Normal Move:
                      </h4>
                      <p className="text-gray-300">
                        Move to any adjacent empty intersection along the lines
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-[#f95e5e] mb-2">
                        Capture Move:
                      </h4>
                      <p className="text-gray-300">
                        Jump over an adjacent goat to an empty point directly
                        behind it. The goat is captured and removed.
                      </p>
                    </div>
                    <div className="bg-[#2f2d2a] p-3 rounded border border-[#3a3835]">
                      <p className="text-gray-400 text-sm">
                        ⚠️ Tigers cannot jump over other tigers or jump to
                        occupied intersections
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-[#262522] border border-[#3a3835] p-6 rounded-lg">
                  <h3 className="text-xl font-semibold text-white mb-4">
                    🐐 Goat Movement
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-[#f95e5e] mb-2">
                        Movement:
                      </h4>
                      <p className="text-gray-300">
                        Move to any adjacent empty intersection along the lines
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-[#f95e5e] mb-2">
                        No Capturing:
                      </h4>
                      <p className="text-gray-300">
                        Goats cannot capture tigers - they win through
                        positioning and blocking
                      </p>
                    </div>
                    <div className="bg-[#2f2d2a] p-3 rounded border border-[#3a3835]">
                      <p className="text-gray-400 text-sm">
                        🤝 Goats must work together to create effective
                        blockades
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-[#262522] p-6 rounded-lg border border-[#3a3835]">
                <h3 className="text-xl font-semibold text-white mb-4">
                  📐 Board Layout
                </h3>
                <div className="space-y-4">
                  <p className="text-gray-300">
                    The board consists of 25 intersection points connected by
                    lines. Pieces can only move along these lines to adjacent
                    intersections.
                  </p>
                  <div className="space-y-3 text-sm text-gray-400">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-[#f95e5e] rounded-full mr-3"></div>
                      <span>Corner points (tiger starting positions)</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-gray-500 rounded-full mr-3"></div>
                      <span>Edge points</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-gray-400 rounded-full mr-3"></div>
                      <span>Center and inner points</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Victory Conditions */}
        <section className="mb-16">
          <div className="bg-[#2f2d2a] rounded-xl shadow-2xl p-8 border border-[#3a3835]">
            <h2 className="text-3xl font-bold text-white mb-6">
              Victory Conditions
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-[#262522] border-l-4 border-[#f95e5e] p-6 rounded-r-lg">
                <h3 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                  🐅 Tigers Win
                </h3>
                <div className="space-y-4">
                  <p className="text-lg text-[#f95e5e] font-medium">
                    Capture 5 goats
                  </p>
                  <p className="text-gray-300">
                    Tigers achieve victory by successfully capturing 5 goats
                    through jumping maneuvers. Each captured goat is permanently
                    removed from the board.
                  </p>
                  <div className="bg-[#2f2d2a] p-4 rounded-lg border border-[#3a3835]">
                    <p className="text-gray-400 text-sm">
                      <strong className="text-white">Strategy:</strong> Focus on
                      creating capture opportunities and avoiding complete
                      encirclement
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#262522] border-l-4 border-[#f95e5e] p-6 rounded-r-lg">
                <h3 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                  🐐 Goats Win
                </h3>
                <div className="space-y-4">
                  <p className="text-lg text-[#f95e5e] font-medium">
                    Block all tiger movements
                  </p>
                  <p className="text-gray-300">
                    Goats win by positioning themselves so that no tiger can
                    make any legal move. This includes both normal moves and
                    capture moves.
                  </p>
                  <div className="bg-[#2f2d2a] p-4 rounded-lg border border-[#3a3835]">
                    <p className="text-gray-400 text-sm">
                      <strong className="text-white">Strategy:</strong>{" "}
                      Coordinate positioning to create impenetrable barriers
                      around tigers
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Strategy Tips */}
        <section className="mb-16">
          <div className="bg-[#2f2d2a] rounded-xl shadow-2xl p-8 border border-[#3a3835]">
            <h2 className="text-3xl font-bold text-white mb-6">
              Strategy Tips
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold text-white mb-4">
                  🐅 Tiger Strategies
                </h3>
                <div className="space-y-3">
                  <div className="bg-[#262522] p-4 rounded-lg border border-[#3a3835]">
                    <h4 className="font-medium text-[#f95e5e] mb-2">
                      Early Game
                    </h4>
                    <p className="text-gray-300 text-sm">
                      Stay mobile and avoid clustering. Look for isolated goats
                      to capture.
                    </p>
                  </div>
                  <div className="bg-[#262522] p-4 rounded-lg border border-[#3a3835]">
                    <h4 className="font-medium text-[#f95e5e] mb-2">
                      Mid Game
                    </h4>
                    <p className="text-gray-300 text-sm">
                      Create threats from multiple directions. Force goats into
                      defensive positions.
                    </p>
                  </div>
                  <div className="bg-[#262522] p-4 rounded-lg border border-[#3a3835]">
                    <h4 className="font-medium text-[#f95e5e] mb-2">
                      Late Game
                    </h4>
                    <p className="text-gray-300 text-sm">
                      Be patient and wait for goat mistakes. Maintain escape
                      routes.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-white mb-4">
                  🐐 Goat Strategies
                </h3>
                <div className="space-y-3">
                  <div className="bg-[#262522] p-4 rounded-lg border border-[#3a3835]">
                    <h4 className="font-medium text-[#f95e5e] mb-2">
                      Placement Phase
                    </h4>
                    <p className="text-gray-300 text-sm">
                      Control the center and limit tiger mobility. Avoid giving
                      easy captures.
                    </p>
                  </div>
                  <div className="bg-[#262522] p-4 rounded-lg border border-[#3a3835]">
                    <h4 className="font-medium text-[#f95e5e] mb-2">
                      Movement Phase
                    </h4>
                    <p className="text-gray-300 text-sm">
                      Work as a team to create walls. Sacrifice position for
                      blocking if necessary.
                    </p>
                  </div>
                  <div className="bg-[#262522] p-4 rounded-lg border border-[#3a3835]">
                    <h4 className="font-medium text-[#f95e5e] mb-2">Endgame</h4>
                    <p className="text-gray-300 text-sm">
                      Tighten the noose gradually. Don't rush and leave escape
                      routes.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Common Mistakes */}
        <section className="mb-8">
          <div className="bg-[#262522] border border-[#3a3835] rounded-xl p-8">
            <h2 className="text-3xl font-bold text-white mb-6">
              Common Mistakes to Avoid
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">
                  🐅 Tiger Mistakes:
                </h3>
                <ul className="space-y-2 text-gray-300">
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Moving tigers too close together</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Ignoring potential encirclement</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Making hasty capture attempts</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Getting trapped in corners</span>
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-4">
                  🐐 Goat Mistakes:
                </h3>
                <ul className="space-y-2 text-gray-300">
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Placing goats in easily captured positions</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Not coordinating movements</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Leaving gaps in defensive lines</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-[#f95e5e] mr-3 mt-1">✗</span>
                    <span>Being too aggressive early</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Rules;
